---
targets: ["*"]
description: "Disables automatic git commit and push actions unless explicitly requested"
globs: ["**/*"]
alwaysApply: true
---

# No auto commit

NEVER commit or push changes unless the user explicitly asks you to do so in that specific request.
Do not assume that because you committed changes once, you should continue committing subsequent changes.
Each commit/push must be explicitly requested by the user for that particular change.
