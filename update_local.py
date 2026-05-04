import tomllib
import tomli_w

with open('.mise.toml', 'rb') as f:
    data = tomllib.load(f)

data['settings']['http_retries'] = 10
data['settings']['locked'] = True

with open('.mise.toml', 'wb') as f:
    tomli_w.dump(data, f)
