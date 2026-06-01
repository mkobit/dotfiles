import json

existing = {"env": {"EXISTING_VAR": "true"}}
managed = {"env": {"DISABLE_TELEMETRY": "true", "ENABLE_TOOL_SEARCH": "auto"}}

# We need a deep merge for dicts like 'env'
def deep_merge(d1, d2):
    for k, v in d2.items():
        if isinstance(v, dict) and k in d1 and isinstance(d1[k], dict):
            deep_merge(d1[k], v)
        else:
            d1[k] = v
    return d1

merged = deep_merge(existing.copy(), managed)
print(json.dumps(merged, indent=2))
