#!/bin/bash
chezmoi -S "$(pwd)/src/chezmoi" execute-template < src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json
