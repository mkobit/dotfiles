"""
Guarded installation rule for dotfiles.

This rule creates an executable that can safely inject configuration content
into existing files using guard comments, allowing for safe incremental
updates without overwriting existing user configurations.
"""

def guarded_install_rule(
        name,
        target_file,
        content,
        header_comment = "#",
        guard_start = "START DOTFILES MANAGED SECTION",
        guard_end = "END DOTFILES MANAGED SECTION",
        **kwargs):
    """Creates a guarded install rule.

    This generates an executable that will:
    1. Check if the target file exists
    2. Look for existing dotfiles managed section
    3. Either create new section or update existing one
    4. Use guard comments to safely manage content

    Args:
        name: Name of the rule
        target_file: Path to the target file (e.g., "~/.gitconfig")
        content: Content file to inject between guards
        header_comment: Comment character(s) to use (default: "#")
        guard_start: Start guard text
        guard_end: End guard text
        **kwargs: Additional arguments passed to sh_binary
    """

    # Create the install script
    script_name = name + "_install_script.sh"
    template_script = "//rules/common:guarded_install_template.sh"

    # Create the install script using the template
    native.genrule(
        name = name + "_script_gen",
        outs = [script_name],
        srcs = [template_script, content],
        cmd = '''
        cp $(location //rules/common:guarded_install_template.sh) $@
        sed -i.bak 's|__TARGET_FILE__|{target_file}|g' $@
        sed -i.bak 's|__HEADER_COMMENT__|{header_comment}|g' $@
        sed -i.bak 's|__GUARD_START__|{guard_start}|g' $@
        sed -i.bak 's|__GUARD_END__|{guard_end}|g' $@
        sed -i.bak 's|__LABEL__|//{package}:{name}|g' $@
        sed -i.bak 's|__CONTENT_FILE__|$(location {content})|g' $@
        rm $@.bak
        chmod +x $@
        '''.format(
            target_file = target_file,
            header_comment = header_comment,
            guard_start = guard_start,
            guard_end = guard_end,
            package = native.package_name(),
            name = name,
            content = content,
        ),
    )

    # Create the executable sh_binary with the script and content file as data
    native.sh_binary(
        name = name,
        srcs = [script_name],
        data = [content],
        env = {
            "BAZEL_CONTENT_FILE": "$(location {})".format(content),
        },
        **kwargs
    )


