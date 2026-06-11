# Documentation and prose style
- Use sentence case for all headers and titles.
- Write documentation (README, HTML, Markdown, and other formats) with one sentence per line.
- Prioritize technical rationale and "why" over "what" in documentation and commit messages.

# Cli design principles
- Design tools with agentic use at the forefront to ensure they are easily scriptable and interpretable by ai.
- Follow the unix philosophy with focused, composable commands that do one thing well.
- Provide rich, colorful terminal output with clear progress indicators for interactive sessions.
- Support both interactive modes and headless/ci-friendly flags for all tools.

# User experience and interface
- Optimize for high-performance terminal emulators like ghostty.
- Prioritize terminal-first design patterns for all developer tools.

# Maintenance and quality standards
- Maintain complete reproducibility across all supported environments (personal, work, remote).
- Reduce code proliferation by agents by focusing on small, composable, and useful tools.
- Focus on correctness in chezmoi by leveraging internal paradigms and validation rules.
- Ensure all changes are validated by the test pipeline before deployment.
