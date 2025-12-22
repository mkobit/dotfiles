# Mise - Polyglot tool version manager

Mise is a fast, polyglot tool version manager.
It can manage versions for a variety of tools like Node.js, Python, Ruby, Go, and more.
It's a replacement for tools like `asdf`, `nvm`, and `pyenv`.

## What it does

- Manages multiple versions of development tools on a per-project basis.
- Uses a `.mise.toml` configuration file to define tool versions.
- Activates and deactivates tool versions automatically when you enter a directory.

### Example usage

A typical `.mise.toml` file might look like this:

```toml
[tools]
node = "20"
python = "3.11"
```

For more advanced usage and a full list of supported tools, please refer to the [official documentation](https://mise.jdx.dev/).

## Installation

Managed via chezmoi external sources.
The binary is downloaded directly from the official GitHub releases.
It is made available in the `{{ .chezmoi.destDir }}/.local/bin` directory.

## Shell integration

Mise hooks into the shell to manage the environment.
Activation is handled by the shell's startup files (e.g., `.zshrc`).

## Links

- [Project homepage](https://github.com/jdx/mise)
- [Official Documentation](https://mise.jdx.dev/)
- [Installation guide](https://mise.jdx.dev/installing-mise.html)
