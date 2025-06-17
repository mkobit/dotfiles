# Dotfiles

Personal dotfiles managed with Bazel for cross-platform configuration management.

## Quick Start

```bash
# Build for personal profile
bazel build //... --//config:profile=personal

# Run tests
bazel test //...

# Install configurations
bazel run //config:install_all
```

## Features

- **Cross-platform**: Supports Linux, macOS, and Windows
- **Profile-based**: Separate personal and work configurations
- **Bazel-managed**: Reproducible builds and dependency management
- **Comprehensive testing**: Quality checks and validation
- **Security-first**: Pinned dependencies and automated security updates

## Security

This repository follows security best practices for CI/CD pipelines:

- **🔒 Pinned Dependencies**: All GitHub Actions pinned to specific commit SHAs
- **🔄 Automated Updates**: Dependabot configured for security updates
- **🛡️ Supply Chain Security**: Minimized attack surface through version pinning
- **📋 Security Documentation**: Detailed practices in [docs/SECURITY.md](docs/SECURITY.md)

Key security implementations:
- Actions pinned to commit hashes (not floating tags)
- Specific runner versions (ubuntu-24.04, macos-15, windows-2022)
- Homebrew install script pinned to specific commit
- Weekly automated security updates via Dependabot

See [docs/SECURITY.md](docs/SECURITY.md) for complete security practices and incident response procedures.

## Configuration Profiles

### Personal Profile
- Development-focused configurations
- Extended shell aliases and functions
- Personal Git settings and tools

### Work Profile
- Corporate-friendly configurations
- Compliance-focused settings
- Professional Git configuration

## Building

```bash
# Build specific profile
bazel build //... --//config:profile=personal
bazel build //... --//config:profile=work

# Run formatting
bazel run //:format

# Generate IDE configuration
bazel run //:lsp_setup
bazel run //:compile_commands
```

## Testing

```bash
# Run all tests
bazel test //...

# Run quality checks
bazel test //:quality_checks

# Coverage report
bazel coverage //...
```

## Development

### Prerequisites
- Bazel 6.0+
- Git
- Platform-specific tools (automatically installed via CI)

### Local Development
```bash
# Format code
bazel run //:format

# Lint and validate
bazel test //:format_test

# Build and test everything
bazel test //...
```

### CI/CD
GitHub Actions workflow handles:
- Multi-platform testing (Ubuntu, macOS, Windows)
- Both personal and work profile validation
- Automated security scanning
- Performance benchmarking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the established patterns
4. Run `bazel test //...` to ensure tests pass
5. Submit a pull request

Please review [docs/SECURITY.md](docs/SECURITY.md) for security practices when contributing.

## License

MIT License - see [LICENSE](LICENSE) for details.
