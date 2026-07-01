import json

# Suppose ConvertTo-Json produced this:
json_output = r'{"input": "\\u001b\\r"}'
print("Before:", json_output)

# Powershell: $json.Replace('\\u001b', '\u001b')
json_output2 = json_output.replace(r'\\u001b', r'\u001b')
print("After replace 1:", json_output2)

# Powershell: $json.Replace('\\r', '\r')
json_output3 = json_output2.replace(r'\\r', r'\r')
print("After replace 2:", json_output3)
