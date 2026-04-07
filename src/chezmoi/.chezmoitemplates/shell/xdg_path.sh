# Add ~/.local/bin to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin:$PATH"
fi

# Add ~/.local/bin/tools to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin/tools" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin/tools:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin/tools:$PATH"
fi

{{- if eq .chezmoi.os "darwin" }}
{{-   if stat "/Applications/Obsidian.app" }}
if [[ ":$PATH:" != *":/Applications/Obsidian.app/Contents/MacOS:"* ]]; then
    export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
fi
{{-   end }}
{{- end }}
