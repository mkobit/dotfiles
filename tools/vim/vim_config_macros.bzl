"""Macros for Vim configuration generation."""

def platform_specific_vim_config(name, platform, config_file):
    """Generate platform-specific vim configuration.
    
    Args:
        name: Target name
        platform: Platform identifier (macos, linux, wsl, etc)
        config_file: Path to platform-specific vim config
    """
    native.genrule(
        name = name,
        srcs = [
            config_file,
            "//modules/vim:vimrc.template",
        ],
        outs = [name + ".vim"],
        cmd = """
            cat $(location //modules/vim:vimrc.template) > $@
            echo "" >> $@
            echo " =============================================" >> $@
            echo " """ + platform.capitalize() + """-specific configuration" >> $@
            echo " =============================================" >> $@
            cat $(location """ + config_file + """) >> $@
            echo "" >> $@
            echo " Generated for """ + platform.capitalize() + """ by Bazel" >> $@
        """,
    )
