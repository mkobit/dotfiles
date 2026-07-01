import json

# if the json file contains literally "\u001b\\r"
j_str = r'{"input": "\u001b\\r"}'
parsed = json.loads(j_str)
print("Parsed string:", repr(parsed["input"]))

# if the json file contains literally "\u001b\r"
j_str2 = r'{"input": "\u001b\r"}'
parsed2 = json.loads(j_str2)
print("Parsed string 2:", repr(parsed2["input"]))
