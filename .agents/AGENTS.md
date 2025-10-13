# Agent context for dotfiles repository

> **Note**: This file is symlinked from `.agents/AGENTS.md` for convenient access from project root.

## Project overview

Personal dotfiles repository using chezmoi for configuration management.
Maintains personal/work profiles with hybrid Bazel automation.

### Responsibilities

#### chezmoi handles:
- Dotfile installation and management (`chezmoi apply`)
- Template processing and variable substitution
- Cross-platform file management
- User-specific configuration deployment

#### Bazel retains:
- **Verification**: Validate configurations before deployment
- **Testing**: Unit tests for configuration logic
- **Automation**: Generate chezmoi files (versions, SHAs, external dependencies)
- **Build reproducibility**: Pinned dependencies and deterministic builds

## Repository structure

- `src/` - Chezmoi templates and deployment configuration
- `tools/` - Bazel rules for validation, testing, and automation
- `config/` - Build configuration and profile management
- chezmoi files - `.chezmoi*` configuration and templates

## Commands

### Primary workflow (chezmoi)
```bash
chezmoi diff                                    # Preview changes
chezmoi apply                                   # Install/update dotfiles
chezmoi edit dot_gitconfig                      # Edit source files
```

### Development (Bazel)
```bash
bazel test //...                                # Run tests
bazel run //:format                             # Format code
```

## Key principles

- Use existing patterns before creating new ones
- Feature flags over profiles for granular configuration control
- Security paramount with pinned versions and no committed secrets
- Cross-platform compatibility (Linux, macOS)
- Preserve existing user configurations during installation

## Configuration patterns

### Feature flags (preferred over profiles)
Use granular feature flags in `.chezmoidata.toml` instead of monolithic profiles:

```toml
# Git personal configuration
[git.personal]
enabled = true
name = "Your Name"
email = "you@example.com"
signing_key = "GPG_KEY_ID"
gpg_sign = true
```

**Benefits:**
- Granular per-feature control
- Easy to disable specific features per machine
- Work environments can override cleanly

### Template auto-discovery

Config templates use `glob` patterns to auto-discover snippet files:

```go
{{/* Auto-sources all .zsh files in snippets directory */}}
{{- range glob (print .chezmoi.homeDir "/.dotfiles/zsh/snippets/*.zsh") }}
source {{ . }}
{{- end }}
```

**Benefits:**
- Future-proof - just drop files in directories
- Template validates existence at build time
- No hardcoded file lists to maintain
- Consistent pattern across zsh/vim/tmux

### Template scoping with `with`

Use `with` for clear scoping and cleaner templates:

```go
{{- with .git.personal }}
{{- if .enabled }}
[user]
  name = {{ .name | quote }}
  email = {{ .email | quote }}
  signingkey = {{ .signing_key }}
{{- end }}
{{- end }}
```

### Hyphenated keys in templates

When accessing keys containing hyphens (e.g., `oh-my-zsh`), use the `index` function:

```go
{{- with (index .zsh "oh-my-zsh") }}
{{- if eq .installation "external-sources" }}
# Template content here
{{- end }}
{{- end }}
```

**Why**: Direct access like `.zsh.oh-my-zsh` causes "bad character U+002D" errors in chezmoi/Go templates.
**Reference**: [Stack Overflow - Helm templating hyphens](https://stackoverflow.com/questions/63853679/helm-templating-doesnt-let-me-use-dash-in-names)

### Early failure validation

Validate required fields early with descriptive error messages:

```go
{{- if .git.personal.enabled }}
{{- if not .git.personal.name }}
{{- fail "git.personal.enabled is enabled but name is empty" }}
{{- end }}
{{- if not .git.personal.email }}
{{- fail "git.personal.enabled is enabled but email is empty" }}
{{- end }}
{{- if not .git.personal.signing_key }}
{{- fail "git.personal.enabled is enabled but signing_key is empty" }}
{{- end }}
{{- end }}
```

### 🚨 Managed environment constraints

We need to operate within environments that have managed infrastructure that handle files typically self-managed in a user controlled system.

**Safe patterns:**
- `modify_` scripts → **ONLY** safe way to customize externally managed `.gitconfig`, `.zshrc`, etc.
- `dot_dotfiles/` → Create your own organized directory structure
- Private files in `~/.dotfiles/` → Full control for non-corporate managed locations

**Forbidden in managed environments:**
- Never use `dot_gitconfig`, `dot_zshrc` when external infrastructure manages these files
- Never replace system binaries or externally-installed tools
- `modify_` scripts are required for any file that corporate IT manages

## Tooling guides

- **jq**: For guidelines on using `jq` and managing custom modules, see [src/dot_dotfiles/jq/jq.md](src/dot_dotfiles/jq/jq.md).
- **Claude Code**: Configuration precedence and agent patterns, see [src/dot_dotfiles/claude-code/claude-code.md](src/dot_dotfiles/claude-code/claude-code.md).
- **iTerm**: Profile management and scripting, see [src/dot_dotfiles/iterm/iterm.md](src/dot_dotfiles/iterm/iterm.md).
- **Rectangle Pro**: Window management automation, see [src/dot_dotfiles/rectangle-pro/rectangle-pro.md](src/dot_dotfiles/rectangle-pro/rectangle-pro.md).
- **Alacritty**: Cross-platform terminal configuration, see [src/dot_dotfiles/alacritty/alacritty.md](src/dot_dotfiles/alacritty/alacritty.md).

## chezmoi documentation

This repository uses chezmoi for dotfiles management.

### Special files
- [Template format](https://www.chezmoi.io/reference/special-files/chezmoi-format-tmpl/) - `.tmpl` files with Go templating
- [Data files](https://www.chezmoi.io/reference/special-files/chezmoidata-format/) - `.chezmoidata.*` for template variables
- [External files](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/) - `.chezmoiexternal.*` for downloaded files
- [Ignore patterns](https://www.chezmoi.io/reference/special-files/chezmoiignore/) - `.chezmoiignore` for exclusions
- [Remove files](https://www.chezmoi.io/reference/special-files/chezmoiremove/) - `.chezmoiremove` for cleanup
- [Root directory](https://www.chezmoi.io/reference/special-files/chezmoiroot/) - `.chezmoiroot` for source location
- [Version requirements](https://www.chezmoi.io/reference/special-files/chezmoiversion/) - `.chezmoiversion` for version constraints

### Special directories
- [Data directory](https://www.chezmoi.io/reference/special-directories/chezmoidata/) - `.chezmoidata/` for template data files
    - "If any .chezmoidata/ directories exist in the source state, all files within them are interpreted as structured static data in the given formats. This data can then be used in templates. See also .chezmoidata.$FORMAT."
- [Externals directory](https://www.chezmoi.io/reference/special-directories/chezmoiexternals/) - `.chezmoiexternals/` for external file configs
    - "If any .chezmoiexternals/ directories exist in the source state, then all files in this directory are treated as .chezmoiexternal.<format> files relative to the source directory."
    - **IMPORTANT**: Always prefer chezmoi externals over custom download scripts for binaries, archives, and files from URLs
    - See [chezmoi externals patterns](#chezmoi-externals-patterns) below for detailed guidance
- [Scripts directory](https://www.chezmoi.io/reference/special-directories/chezmoiscripts/) - `.chezmoiscripts/` for run scripts
    - "If a directory called .chezmoiscripts/ exists in the root of the source directory, then any scripts in it are executed as normal scripts without creating a corresponding directory in the target state. The run_ attribute is still required."
- [Templates directory](https://www.chezmoi.io/reference/special-directories/chezmoitemplates/) - `.chezmoitemplates/` for reusable templates
    - "If any directory called .chezmoitemplates/ exists in the source state, then all files in this directory are available as templates with a name equal to the relative path to the .chezmoitemplates/ directory."
    - "The template action or includeTemplate function can be used to include these templates in another template. The context value (.) must be set explicitly if needed, otherwise the template will be executed with nil context data."

### Configuration
- [Configuration file](https://www.chezmoi.io/reference/configuration-file/) - `.chezmoi.toml` settings

### Core concepts
- [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/) - File prefixes/suffixes (dot_, create_, encrypted_, executable_, etc.)
- [Application order](https://www.chezmoi.io/reference/application-order/) - Deterministic processing: before scripts → directories → files → after scripts (alphabetical)
- [Target types](https://www.chezmoi.io/reference/target-types/) - Files, directories, symlinks, scripts with type-specific attributes
- [Template functions](https://www.chezmoi.io/reference/templates/functions/) - Sprig functions + chezmoi-specific (includeTemplate, lookPath, output, etc.)
- [Template variables](https://www.chezmoi.io/reference/templates/variables/) - Complete variable reference

**Key template variables**:
- `{{ .chezmoi.sourceFile }}` - Current template source file path (e.g., `modify_dot_gitconfig.tmpl`)
- `{{ .chezmoi.sourceDir }}` - Source directory path (e.g., `/Users/user/.local/share/chezmoi/src`)
- `{{ .chezmoi.homeDir }}` - User home directory path (e.g., `/Users/user`)
- `{{ .chezmoi.hostname }}` - Machine hostname
- `{{ .chezmoi.username }}` - Current user
- `{{ .chezmoi.os }}` - Operating system (darwin, linux, windows)
- `{{ .chezmoi.arch }}` - Architecture (amd64, arm64)

**Note**: Raw markdown documentation is also available at [chezmoi source docs](https://github.com/twpayne/chezmoi/tree/master/assets/chezmoi.io) for more concise reference when working with agents.

## chezmoi externals patterns

**CRITICAL**: Always use chezmoi externals (`.chezmoiexternals/`) for downloading binaries, archives, and files from URLs. Never write custom curl/wget download scripts.

### Directory structure

```
src/
├── dot_local/bin/.chezmoiexternals/
│   ├── fzf.toml.tmpl      # Binary to ~/.local/bin/fzf
│   ├── asdf.toml.tmpl     # Binary to ~/.local/bin/asdf
│   └── jq.toml.tmpl       # Binary to ~/.local/bin/jq
└── .chezmoidata.toml       # Version and checksum data
```

### Basic patterns

**Single binary from tar.gz archive:**
```toml
{{- with .fzf -}}
{{- if eq .installation "external-sources" -}}
{{- $platform := printf "%s_%s" $.chezmoi.os $.chezmoi.arch }}
["fzf"]
type = "archive-file"
url = {{ gitHubReleaseAssetURL "junegunn/fzf" (printf "v%s" .version) (printf "fzf-%s-%s_%s.tar.gz" .version $.chezmoi.os $.chezmoi.arch) | quote }}
path = "fzf"
executable = true
checksum.sha256 = "{{ index .checksums $platform }}"
{{- end -}}
{{- end }}
```

**With custom target platform names:**
```toml
{{- with .eza -}}
{{- if eq (index .installation $.chezmoi.os) "external-sources" -}}
{{- $platform := printf "%s_%s" $.chezmoi.os $.chezmoi.arch -}}
{{- $target := "" -}}
{{- if eq $.chezmoi.os "linux" -}}
  {{- if eq $.chezmoi.arch "arm64" -}}
    {{- $target = "aarch64-unknown-linux-gnu" -}}
  {{- else -}}
    {{- $target = "x86_64-unknown-linux-musl" -}}
  {{- end -}}
{{- else if eq $.chezmoi.os "darwin" -}}
  {{- if eq $.chezmoi.arch "arm64" -}}
    {{- $target = "aarch64-apple-darwin" -}}
  {{- else -}}
    {{- $target = "x86_64-apple-darwin" -}}
  {{- end -}}
{{- end -}}
["eza"]
type = "archive-file"
url = {{ gitHubReleaseAssetURL "eza-community/eza" (printf "v%s" .version) (printf "eza_%s.tar.gz" $target) | quote }}
path = "eza"
executable = true
checksum.sha256 = "{{ index .checksums $platform }}"
{{- end -}}
{{- end }}
```

### Data file format

Store versions and checksums in `.chezmoidata.toml`:

```toml
[fzf]
version = "0.65.2"
installation = "external-sources"

[fzf.checksums]
darwin_arm64 = "a1464f1d4b75c3a92975f67055f9e407800ed35820ea7d73f2afb90aeb0491e8"
darwin_amd64 = "3bb8b0e746b6238aa2ce43550c06f16a81fc9a46687b06456d996cb54be762e4"
linux_amd64 = "5eb8efc0e94aa559f84ea83eeba99bea7dce818e63f92b4b62e60663220f1c14"
linux_arm64 = "097347160595bf03a426d2abe0a17e14ca060540ddfc0ea45c0a9be62bb29a2b"
```

### Key fields reference

- `type`: `"file"` (single file), `"archive"` (full archive), `"archive-file"` (one file from archive)
- `url`: Download URL, use `gitHubReleaseAssetURL` helper for GitHub releases
- `executable`: `true` for binaries
- `path`: Path within archive for `archive-file` type
- `stripComponents`: Remove N leading path components from archive
- `checksum.sha256`: SHA256 checksum for verification
- `refreshPeriod`: How often to check for updates (e.g., `"720h"` = 30 days)

### When to use externals vs scripts

**Use chezmoi externals for:**
- GitHub release binaries
- Pre-compiled binaries from URLs
- Archives that need extraction
- Single files from URLs

**Use run_once scripts for:**
- Plugin management (e.g., asdf plugins)
- Complex multi-step configuration
- Installation requiring compilation
- Package manager installations

### Unsupported compression formats

For unsupported archive formats, see [chezmoi docs on custom filters](https://www.chezmoi.io/user-guide/include-files-from-elsewhere/#handle-tar-archives-in-an-unsupported-compression-format).

## chezmoi script patterns

### Shared utility libraries

For reusable code across multiple scripts, use the `scripts/` directory pattern:

```bash
# Structure
src/
├── scripts/
│   └── logging.sh            # Shared logging utilities
└── .chezmoiscripts/
    └── run_once_example.sh.tmpl

# Usage in scripts
#!/bin/bash
# logging.sh hash: {{ include "scripts/logging.sh" | sha256sum }}
source "${CHEZMOI_SOURCE_DIR:?}/scripts/logging.sh"

log_info "Using shared logging utilities..."
```

**Key principles:**
- Use `${CHEZMOI_SOURCE_DIR:?}` for robust sourcing with error handling
- Include hash comments for dependency tracking (script re-runs when utilities change)
- Keep utilities in `scripts/` directory (not managed as dotfiles)
- Follow community pattern from [chezmoi/discussions/3506](https://github.com/twpayne/chezmoi/discussions/3506)

See `src/scripts/logging.sh` for available functions.

## Chezmoi modify script essentials

**Key insight**: `modify_` scripts work on ANY file via stdin/stdout - perfect for adding sections to corporate-managed files.

**Critical components**:
1. **SHA256 hash in header/footer** - enables change detection and re-execution
2. **Replacement logic with sed** - removes old sections before adding new ones
3. **Matching header/footer** - defines exact boundaries for replacement
4. **ISO8601 timestamp** - shows when section was last applied

**Header pattern**:
```bash
# /path/to/script.tmpl:BEGIN:section:12345678 - WARNING: managed by chezmoi, do not edit
# Applied: 2025-01-15T10:30:45Z07:00
[configuration]
# /path/to/script.tmpl:END:section:12345678
```

**BSD sed compatibility**: Use literal filenames in sed patterns, not template variables (they expand incorrectly).

## General Agentic Guidance

When undertaking any task, it is crucial to begin by thoroughly understanding the request and the context of the repository. Follow these steps to ensure a successful and efficient workflow:

1.  **Understand the Goal:** Before writing any code, take the time to understand the user's ultimate objective. If the request is ambiguous, ask clarifying questions.

2.  **Explore the Codebase:**
    *   Get a comprehensive overview of the repository structure.
    *   Read the `AGENTS.md` file (this file) to understand project-specific guidelines, architecture, and key principles.
    *   Examine relevant configuration files (e.g., `chezmoi.toml`, `BUILD.bazel`) to understand how the project is set up.
    *   Pay special attention to the `src/` directory, as it is the chezmoi root and contains the core dotfile templates.

3.  **Formulate a Plan:**
    *   Create a step-by-step plan that outlines your approach.
    *   Include steps for verification, such as running tests or inspecting files, to confirm that your changes have been applied correctly.
    *   Formalize your plan before starting work.

4.  **Execute and Verify:**
    *   Execute each step of your plan methodically.
    *   After each modification, verify the changes using the available tools.
    *   Do not proceed to the next step until you have confirmed that the previous step was successful.

5.  **Seek Feedback:**
    *   Before submitting your changes, request a code review to get feedback on your work.
    *   Address any issues raised in the review before finalizing your changes.
