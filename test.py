import subprocess
import json

ps_script = """
$newAction = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = '\u001b\r'
    }
}
$json = $newAction | ConvertTo-Json -Depth 20
Write-Host "Raw JSON:"
Write-Host $json
$json = $json.Replace('\\u001b', '\u001b')
Write-Host "Replaced JSON:"
Write-Host $json
"""

with open("test.ps1", "w") as f:
    f.write(ps_script)

subprocess.run(["powershell.exe", "-NoProfile", "-File", "test.ps1"])
