import re

with open('src/chezmoi/.chezmoidata/fzf.toml', 'r') as f:
    content = f.read()

content = re.sub(r'version = "[0-9\.]+"', 'version = "0.70.0"', content)

with open('src/chezmoi/.chezmoidata/fzf.toml', 'w') as f:
    f.write(content)
