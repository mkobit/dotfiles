"""
Include-based installation rules for dotfiles management.

Injects include directives that point to Bazel-built configuration files,
rather than injecting the content directly.
"""

def _include_install_impl(ctx):
    """Implementation for include_install."""

    # Get the template and substitute values
    template = ctx.file._template
    output_script = ctx.actions.declare_file(ctx.label.name + "_install_script.sh")

    # Get the path to the content file
    content_file_path = ""
    if ctx.file.config:
        content_file_path = ctx.file.config.short_path

    # Prepare substitutions
    substitutions = {
        "__TARGET_FILE__": ctx.attr.target_file,
        "__IDENTIFIER__": ctx.attr.identifier,
        "__HEADER_COMMENT__": ctx.attr.header_comment,
        "__LABEL__": str(ctx.label),
        "__CONFIG_FILE_PATH__": content_file_path,
        "__BACKUP__": "true" if ctx.attr.backup else "false",
        "__CREATE_IF_MISSING__": "true" if ctx.attr.create_if_missing else "false",
    }

    # Create the script from template
    ctx.actions.expand_template(
        template = template,
        output = output_script,
        substitutions = substitutions,
        is_executable = True,
    )

    # Collect runfiles
    runfiles = ctx.runfiles(files = [output_script])
    if ctx.file.config:
        runfiles = runfiles.merge(ctx.runfiles(files = [ctx.file.config]))

    return [DefaultInfo(
        executable = output_script,
        runfiles = runfiles,
    )]

def include_install(
    name,
    target_file,
    config,
    identifier,
    header_comment = "#",
    backup = False,
    create_if_missing = True,
    **kwargs):
    """
    Creates an include installation rule that injects include directives.

    Args:
        name: Name of the rule
        target_file: Path to the target file (supports ~ expansion)
        config: Label of the Bazel-built configuration file to include
        identifier: Unique identifier for this include directive
        header_comment: Comment character for the target file type
        backup: Whether to create backup files
        create_if_missing: Whether to create the target file if it doesn't exist
        **kwargs: Additional arguments passed to the rule
    """

    # Create the rule
    _include_install_rule(
        name = name,
        target_file = target_file,
        config = config,
        identifier = identifier,
        header_comment = header_comment,
        backup = backup,
        create_if_missing = create_if_missing,
        **kwargs
    )

_include_install_rule = rule(
    implementation = _include_install_impl,
    attrs = {
        "target_file": attr.string(mandatory = True),
        "config": attr.label(allow_single_file = True, mandatory = True),
        "identifier": attr.string(mandatory = True),
        "header_comment": attr.string(default = "#"),
        "backup": attr.bool(default = False),
        "create_if_missing": attr.bool(default = True),
        "_template": attr.label(
            default = "//rules/common:include_install_template.sh",
            allow_single_file = True,
        ),
    },
    executable = True,
)
