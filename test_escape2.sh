#!/bin/bash
CMD="
    \$newAction = [PSCustomObject]@{
        command = [PSCustomObject]@{
            action = 'sendInput'
            input = '\u001b\r'
        }
        id = \$targetActionId
        keys = 'shift+enter'
    }

    \$json = \$json.Replace('\\u001b', '\u001b')
"
echo "$CMD"
