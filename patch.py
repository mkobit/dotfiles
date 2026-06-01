import json

existing = {"env": {"EXISTING": "true"}}
managed = {"env": {"DISABLE_TELEMETRY": "true"}}

if "env" not in managed:
    managed["env"] = {}
managed["env"]["ENABLE_TOOL_SEARCH"] = "true"

merged = {**existing, **managed}
print(json.dumps(merged, indent=2))
