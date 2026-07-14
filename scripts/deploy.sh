#!/usr/bin/env bash
set -euo pipefail

readonly APP_DIR="/root/inventory_web/prod"
readonly SERVICE_NAME="inventory-web.service"
readonly EXPECTED_SHA="${1:-}"

cd "$APP_DIR"

if [[ -n "$EXPECTED_SHA" ]]; then
    actual_sha="$(git rev-parse HEAD)"
    if [[ "$actual_sha" != "$EXPECTED_SHA" ]]; then
        echo "Expected commit $EXPECTED_SHA, but production is at $actual_sha." >&2
        exit 1
    fi
fi

export PATH="$HOME/.local/bin:$PATH"
uv sync --frozen
.venv/bin/python manage.py migrate --noinput
systemctl restart "$SERVICE_NAME"

if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

for _ in {1..10}; do
    if curl --fail --silent --show-error --max-time 2 --output /dev/null http://127.0.0.1:8000/; then
        echo "Deployment completed: $(git rev-parse --short HEAD)"
        exit 0
    fi
    sleep 1
done

echo "The service did not become ready within 10 seconds." >&2
systemctl status "$SERVICE_NAME" --no-pager
exit 1
