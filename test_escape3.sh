#!/bin/bash
CMD="
    \$newAction = [PSCustomObject]@{
        command = [PSCustomObject]@{
            action = 'sendInput'
            input = '\\u001b[13;2u'
        }
        id = \$targetActionId
        keys = 'shift+enter'
    }

    \$json = \$json.Replace('\\\\u001b', '\\u001b')
"
echo "$CMD"
