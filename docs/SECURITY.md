# Security Practices

This document outlines the security practices implemented in this repository, particularly around version pinning and supply chain security.

## GitHub Actions Security

### Pinned Actions

All GitHub Actions in this repository are pinned to specific commit SHAs for maximum security:

- **actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683** # v4.2.2
- **actions/upload-artifact@84480863f228bb9747b473957fcc9e309aa96097** # v4.4.3
- **actions/cache@6849a6489940f00c2f30c0fb92c6274307ccb58a** # v4.1.2
- **bazel-contrib/setup-bazel@e8776f58fb6a6e9055cbaf1b38c52ccc5247e9c4** # v0.8.1

### Pinned Runner Images

We use specific runner versions instead of `latest` tags:

- **ubuntu-24.04** (instead of ubuntu-latest)
- **macos-15** (instead of macos-latest)
- **windows-2022** (instead of windows-latest)

## Package Management Security

### Pinned Components

1. **Homebrew Install Script**: Pinned to commit `1b02e7dcc5c8cbe8c8be12bb5502fab4fb14b13b`
2. **GitHub Actions**: All pinned to specific commit SHAs

### Cannot Be Pinned (and why)

Some components cannot be practically pinned due to their nature:

1. **Package Manager Repositories**:
   - `apt-get install` (Ubuntu packages)
   - `brew install` (Homebrew packages)
   - `choco install` (Chocolatey packages)

   **Why**: These rely on external package repositories that don't support commit-based pinning. The trade-off is between security and usability.

2. **Runtime-Generated Tools**:
   - Bazel-built binaries
   - Dynamic configuration files

   **Why**: These are generated at runtime based on source code and cannot be pre-pinned.

## Automated Security Updates

### Dependabot Configuration

Dependabot is configured to automatically create PRs for:

- GitHub Actions updates (weekly on Mondays)
- Security vulnerability patches

Configuration: `.github/dependabot.yml`

### Update Process

1. **Dependabot** creates PR with updated commit SHA
2. **Security Review**: Manually review the GitHub compare link
3. **Test**: Automated tests run on the PR
4. **Merge**: After approval and tests pass

## Security Best Practices

### For Contributors

1. **Never use floating tags** (`@main`, `@latest`) for GitHub Actions
2. **Review Dependabot PRs** by checking the GitHub compare link
3. **Test changes** in non-production environments first
4. **Report security issues** privately via GitHub Security tab

### For Maintainers

1. **Regular audits**: Review pinned versions quarterly
2. **Monitor advisories**: Subscribe to security advisories for used actions
3. **Validate updates**: Always check the diff when updating pinned versions
4. **Emergency updates**: Have a process for urgent security patches

## Incident Response

### If a Pinned Action is Compromised

1. **Assess impact**: Check if we're using the compromised version
2. **Emergency pin**: Pin to a known-good version if needed
3. **Update documentation**: Record the incident and response
4. **Review process**: Improve pinning practices if necessary

### If an Unpinned Dependency is Compromised

1. **Immediate action**: Pin to last known-good version
2. **Assessment**: Determine scope of potential impact
3. **Update**: Move to secure version when available
4. **Prevention**: Add to pinning strategy if possible

## Security Contacts

- **Repository Owner**: @mikekobit
- **Security Issues**: Use GitHub Security tab for private disclosure
- **General Questions**: Create issue with `security` label

## References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Supply Chain Security Best Practices](https://slsa.dev/)

---

**Last Updated**: 2025-01-16
**Next Review**: 2025-04-16
