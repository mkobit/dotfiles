#!/bin/bash
CMD="
\$obj = [PSCustomObject]@{
    command = [PSCustomObject]@{
        action = 'sendInput'
        input = '\\u001b[13;2u'
    }
}
\$json = \$obj | ConvertTo-Json -Depth 20
\$json = \$json.Replace('\\\\u001b', '\\u001b')
Write-Host \$json
"
echo "$CMD"
