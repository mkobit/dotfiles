import json

settings = {
    "actions": [
        {
            "command": {
                "action": "sendInput",
                "input": "\\u001b\\r"
            },
            "id": "User.sendInput.shiftEnter",
            "keys": "shift+enter"
        }
    ]
}

j = json.dumps(settings, indent=2)
print("Before:")
print(j)

j = j.replace("\\\\u001b", "\\u001b")
j = j.replace("\\\\r", "\\r")

print("After:")
print(j)
