# Primary languages
- Python 3.13 (Upgrading to 3.14 soon): The primary language for all custom cli tools and ai-powered utilities.
- Shell (zsh, bash): Used for system-level configuration and script automation.

# Build and deployment tools
- Bazel: The build and test orchestration tool for all components.
- Chezmoi: The primary tool for managing dotfiles and application configuration templates.

# Python framework and libraries
- Click / typer: Frameworks for building high-quality cli tools with rich interactivity.
- Pydantic / jsonschema: Used for strict data validation and schema-driven configuration.
- Faster-whisper: Library for efficient ai-powered audio transcription.
- Aiohttp: The standard library for asynchronous http networking.
- Jinja2: Used for template-driven file generation within chezmoi and python tools.

# Quality and testing suite
- Pytest: The primary testing framework for python components.
- Ruff: A fast, all-in-one linter and formatter for python code.
- Mypy: Used for strict static type checking in all python modules.

# Target infrastructure
- Linux: The primary target platform for deployment and use.
- Ghostty: The optimized terminal emulator for high-performance use.
