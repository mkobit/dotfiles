$newAction = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = '\u001b[13;2u'
    }
}
$json = $newAction | ConvertTo-Json -Depth 20
Write-Host "Original JSON:"
Write-Host $json
$json2 = $json.Replace('\\u001b', '\u001b')
Write-Host "Replaced JSON:"
Write-Host $json2
