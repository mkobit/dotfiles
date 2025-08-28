"""
Simplified common utilities using Python execution.

This module provides cleaner, more maintainable rule implementations
that use Python instead of complex shell scripting.
"""

def create_config_rule_py(
        rule_name,
        file_extension,
        mnemonic,
        allowed_extensions = None,
        header_template = None,
        footer_template = None):
    """Creates a configuration rule using Python execution.

    Args:
        rule_name: Name of the rule
        file_extension: Extension for output file (e.g., ".zsh", ".gitconfig")
        mnemonic: Mnemonic for the action
        allowed_extensions: List of allowed file extensions for sources
        header_template: Template for header comment
        footer_template: Template for footer comment

    Returns:
        A rule implementation function
    """

    def _impl(ctx):
        output = ctx.actions.declare_file(ctx.label.name + file_extension)

        # Build list of input files
        input_files = []
        for src in ctx.attr.srcs:
            input_files.extend(src.files.to_list())

        # Build arguments for the Python script
        args = [
            "--output",
            output.path,
            "--inputs",
        ]
        args.extend([f.path for f in input_files])
        args.extend([
            "--rule-name",
            rule_name,
            "--file-extension",
            file_extension,
        ])

        if header_template:
            args.extend(["--header-template", header_template])
        if footer_template:
            args.extend(["--footer-template", footer_template])
        if ctx.attr.header:
            args.extend(["--custom-header", ctx.attr.header])
        if ctx.attr.footer:
            args.extend(["--custom-footer", ctx.attr.footer])

        # Run the Python config generator
        ctx.actions.run(
            outputs = [output],
            inputs = input_files,
            executable = ctx.executable._config_generator,
            arguments = args,
            mnemonic = mnemonic,
            progress_message = "Generating {} configuration %s".format(rule_name) % output.short_path,
        )

        return [DefaultInfo(
            files = depset([output]),
            runfiles = ctx.runfiles(files = [output]),
        )]

    # Define standard attributes
    attrs = {
        "srcs": attr.label_list(
            doc = "Input {} configuration files to be combined".format(rule_name),
            allow_files = allowed_extensions or True,
            mandatory = True,
        ),
        "header": attr.string(
            doc = "Optional header to include at the top of the generated config",
            default = "",
        ),
        "footer": attr.string(
            doc = "Optional footer to include at the end of the generated config",
            default = "",
        ),
        "_config_generator": attr.label(
            default = "//rules/common:config_generator",
            executable = True,
            cfg = "exec",
        ),
    }

    return rule(
        implementation = _impl,
        attrs = attrs,
    )
