import re

with open('src/python/claude_statusline/claude_statusline/main.py', 'r') as f:
    content = f.read()

# Instant.now().add(duration) is failing pyright, let's look at whenever.Instant methods.
# To add a TimeDelta to an Instant, we should just use the `+` operator.
# Or `Instant.now() + duration`. Let's use the `+` operator.

content = content.replace('Instant.now().add(duration)', 'Instant.now() + duration')

with open('src/python/claude_statusline/claude_statusline/main.py', 'w') as f:
    f.write(content)
