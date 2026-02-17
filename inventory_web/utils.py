from typing import Union, List


EmailRecipients = Union[str, List[str]]


def normalize_emails(value: EmailRecipients | None) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return value