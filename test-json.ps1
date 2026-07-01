$obj = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = '\u001b\r'
    }
    id = 'User.sendInput.shiftEnter'
    keys = 'shift+enter'
}
$json = $obj | ConvertTo-Json -Depth 20
$json2 = $json.Replace('\u001b', 'ESC').Replace('\r', 'CR')
Write-Host "json raw:"
Write-Host $json
