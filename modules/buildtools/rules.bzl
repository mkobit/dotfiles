"""
Rules for using buildtools in the dotfiles repository.
"""

BuildtoolsInfo = provider(
    doc = "Information about buildtools configuration",
    fields = {
        "buildifier": "Buildifier target",
        "unused_deps": "Unused deps target",
    },
)

def buildtools_config(name, buildifier = None, unused_deps = None):
    """
    Creates a configuration target for buildtools.
    
    Args:
        name: Name of the target
        buildifier: Override for buildifier target
        unused_deps: Override for unused_deps target
    """
    buildifier = buildifier or "@buildtools//buildifier"
    unused_deps = unused_deps or "@buildtools//unused_deps"
    
    native.alias(
        name = name + "_buildifier",
        actual = buildifier,
        visibility = ["//visibility:public"],
    )
    
    native.alias(
        name = name + "_unused_deps",
        actual = unused_deps,
        visibility = ["//visibility:public"],
    )
    
    native.filegroup(
        name = name,
        srcs = [],
        visibility = ["//visibility:public"],
        tags = ["buildtools_config"],
    )