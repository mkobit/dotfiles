# Common helper rules and macros for dotfiles management

def template_file(name, src, out, substitutions = None):
    """Process a template file with optional substitutions.

    Args:
        name: Target name
        src: Source template file
        out: Output file name
        substitutions: Dictionary of substitutions to apply (optional)
    """
    if substitutions:
        native.genrule(
            name = name,
            srcs = [src],
            outs = [out],
            cmd = "cp $< $@ && " + " && ".join([
                "sed -i.bak 's|{}|{}|g' $@".format(k, v)
                for k, v in substitutions.items()
            ]) + " && rm -f $@.bak",
        )
    else:
        native.genrule(
            name = name,
            srcs = [src],
            outs = [out],
            cmd = "cp $< $@",
        )

def platform_select(options):
    """Select different values based on the platform.

    Args:
        options: Dict with "linux", "macos", "windows" keys and their values

    Returns:
        The appropriate value for the current platform
    """
    return select({
        "@platforms//os:linux": options.get("linux", options.get("default", "")),
        "@platforms//os:macos": options.get("macos", options.get("default", "")),
        "@platforms//os:windows": options.get("windows", options.get("default", "")),
        "//conditions:default": options.get("default", ""),
    })
