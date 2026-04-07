{{- if eq .chezmoi.os "darwin" }}
{{-   if stat "/Applications/Obsidian.app" }}
if [[ ":$PATH:" != *":/Applications/Obsidian.app/Contents/MacOS:"* ]]; then
    export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"
fi
{{-   end }}
{{- end }}
