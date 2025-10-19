# Mise - Polyglot tool version manager

Mise is a fast, polyglot tool version manager. It can manage versions for a variety of tools like Node.js, Python, Ruby, Go, and more. It's a replacement for tools like `asdf`, `nvm`, and `pyenv`.

## What it does

- Manages multiple versions of development tools on a per-project basis.
- Uses a `.mise.toml` configuration file to define tool versions.
- Activates and deactivates tool versions automatically when you enter a directory.
- Fast and written in Rust.

## Installation

Managed via chezmoi external sources. The binary is downloaded directly from the official GitHub releases and made available in the `~/.local/bin` directory.

## Shell Integration

Mise hooks into the shell to manage the environment. Activation is handled by the shell's startup files (e.g., `.zshrc`).

## Links

- [Project homepage](https://github.com/jdx/mise)
- [Official Documentation](https://mise.jdx.dev/)
- [Installation guide](https://mise.jdx.dev/installing-mise.html)