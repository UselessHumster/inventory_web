# Fill in these variables before running the script.
$ApiKey = "PASTE_COMPANY_API_KEY_HERE"
$SourceFolder = "C:\Path\To\BitLockerKeys"
$ApiUrl = "https://YOUR-INVENTORY-DOMAIN/api/bitlocker-keys"

$RecoveryKeyPattern = "\b\d{6}(?:-\d{6}){7}\b"

if ([string]::IsNullOrWhiteSpace($ApiKey) -or $ApiKey -eq "PASTE_COMPANY_API_KEY_HERE") {
    throw "Set the company API key in `$ApiKey before running the script."
}

if ($ApiUrl -match "YOUR-INVENTORY-DOMAIN") {
    throw "Set the inventory API URL in `$ApiUrl before running the script."
}

if (-not (Test-Path -LiteralPath $SourceFolder -PathType Container)) {
    throw "Source folder does not exist: $SourceFolder"
}

$headers = @{ "X-API-Key" = $ApiKey }
$successCount = 0
$skippedCount = 0
$failedCount = 0

foreach ($file in Get-ChildItem -LiteralPath $SourceFolder -File -Filter "*.txt") {
    $nameParts = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) -split "\s+"

    if ($nameParts.Count -lt 2 -or [string]::IsNullOrWhiteSpace($nameParts[1])) {
        Write-Warning "Skipped '$($file.Name)': serial number is missing from the file name."
        $skippedCount++
        continue
    }

    $serialNumber = $nameParts[1].Trim()
    $content = Get-Content -LiteralPath $file.FullName -Raw
    $match = [regex]::Match($content, $RecoveryKeyPattern)

    if (-not $match.Success) {
        Write-Warning "Skipped '$($file.Name)': BitLocker Recovery Password was not found."
        $skippedCount++
        continue
    }

    $body = @{
        serial_number = $serialNumber
        bitlocker_key = $match.Value
    } | ConvertTo-Json -Compress

    try {
        $response = Invoke-RestMethod `
            -Method Post `
            -Uri $ApiUrl `
            -Headers $headers `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop

        $action = if ($response.created) { "created" } else { "updated" }
        Write-Host "[$action] $serialNumber ($($file.Name))" -ForegroundColor Green
        $successCount++
    }
    catch {
        $statusCode = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { "n/a" }
        $details = $_.ErrorDetails.Message
        $message = if ($details) { $details } else { $_.Exception.Message }
        Write-Error "Failed '$($file.Name)' (serial $serialNumber, HTTP $statusCode): $message"
        $failedCount++
    }
}

Write-Host "Completed. Uploaded: $successCount; skipped: $skippedCount; failed: $failedCount."

if ($failedCount -gt 0) {
    exit 1
}
