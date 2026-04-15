import re

with open('./src/chezmoi/dot_config/starship.toml', 'r') as f:
    text = f.read()

# Let's see if the layout looks good.
print(text)
