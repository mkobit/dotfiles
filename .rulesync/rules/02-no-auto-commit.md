---
root: false
targets: ["*"]
description: "Never commit or push unless explicitly asked"
globs: ["**/*"]
cursor:
  alwaysApply: true
  description: "Never commit or push unless explicitly asked"
  globs: ["*"]
---

# No automatic commits

Never commit or push changes unless the user explicitly asks you to do so in that specific request.
Do not assume that because you committed changes once, you should continue committing subsequent changes.
Each commit or push must be explicitly requested by the user for that particular change.
