import re
import os

# 1. Fix gh.toml.tmpl
gh_path = "src/chezmoi/dot_local/bin/.chezmoiexternals/gh.toml.tmpl"
with open(gh_path, "r") as f:
    gh_content = f.read()

gh_content = gh_content.replace(
"""{{- $gh := dict
    "type" "archive-file"
    "url" (gitHubReleaseAssetURL "cli/cli" (printf "v%s" .version) $archive_name)
-}}""",
"""{{- $gh := dict
    "type" "archive-file"
    "url" (gitHubReleaseAssetURL "cli/cli" (printf "v%s" .version) $archive_name)
    "path" $archive_path
    "executable" true
-}}""")

with open(gh_path, "w") as f:
    f.write(gh_content)


# 2. Fix claude-plugins.toml.tmpl indentation
claude_path = "src/chezmoi/dot_local/share/ai/.chezmoiexternals/claude-plugins.toml.tmpl"
with open(claude_path, "r") as f:
    claude_content = f.read()

claude_content = claude_content.replace(
"""    {{- $plugin := dict
    "type" "file"
    "url" (printf "https://raw.githubusercontent.com/%s/%s/%s" .repo .commit .path)
    "checksum" (dict "sha256" .sha256)
-}}""",
"""    {{- $plugin := dict
        "type" "file"
        "url" (printf "https://raw.githubusercontent.com/%s/%s/%s" .repo .commit .path)
        "checksum" (dict "sha256" .sha256)
    -}}""")

with open(claude_path, "w") as f:
    f.write(claude_content)


# 3. Fix fonts.toml.tmpl indentation
fonts_path = "src/chezmoi/dot_local/share/fonts/.chezmoiexternals/fonts.toml.tmpl"
with open(fonts_path, "r") as f:
    fonts_content = f.read()

fonts_content = fonts_content.replace(
"""    {{- $fontConfig := dict
    "type" "archive"
    "url" (printf "https://github.com/ryanoasis/nerd-fonts/releases/download/%s/%s.tar.xz" $font.version $font.name)
    "exact" true
    "checksum" (dict "sha256" $font.sha256)
-}}""",
"""    {{- $fontConfig := dict
        "type" "archive"
        "url" (printf "https://github.com/ryanoasis/nerd-fonts/releases/download/%s/%s.tar.xz" $font.version $font.name)
        "exact" true
        "checksum" (dict "sha256" $font.sha256)
    -}}""")

with open(fonts_path, "w") as f:
    f.write(fonts_content)
