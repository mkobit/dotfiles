#!/bin/bash
powershell.exe -NoProfile -Command "
\$obj = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = \"`u{001b}[13;2u\"
    }
}
\$json = \$obj | ConvertTo-Json -Depth 20
Write-Host \$json
"
