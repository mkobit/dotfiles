
$newAction = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = ''
    }
}
$json = $newAction | ConvertTo-Json -Depth 20
Write-Host "Raw JSON:"
Write-Host $json
$json = $json.Replace('\u001b', '')
Write-Host "Replaced JSON:"
Write-Host $json
