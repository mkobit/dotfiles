import re

with open('src/python/claude_statusline/claude_statusline/segments/claude.py', 'r') as f:
    content = f.read()

content = content.replace("Segment(", "generator=\"internal.claude\", Segment(")
content = content.replace("segment=generator=\"internal.claude\", Segment(", "segment=Segment(")
content = content.replace("segment=Segment(", "generator=\"internal.claude\",\n        segment=Segment(")

with open('src/python/claude_statusline/claude_statusline/segments/claude.py', 'w') as f:
    f.write(content)

with open('src/python/claude_statusline/claude_statusline/segments/workspace.py', 'r') as f:
    content = f.read()

content = content.replace("segment=Segment(", "generator=\"internal.workspace\",\n        segment=Segment(")

with open('src/python/claude_statusline/claude_statusline/segments/workspace.py', 'w') as f:
    f.write(content)
