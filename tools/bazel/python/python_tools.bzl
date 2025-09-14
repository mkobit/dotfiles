"""
Combined Python tooling aspects and rules for linting and type checking.
"""

def _python_tools_test_impl(ctx):
    """Implementation for python_tools_test rule."""

    # This rule doesn't produce any outputs directly
    # The aspects attached to it will do the actual work
    return [DefaultInfo()]

python_tools_test = rule(
    implementation = _python_tools_test_impl,
    attrs = {
        "targets": attr.label_list(
            doc = "Python targets to run tools on",
            providers = [PyInfo],
        ),
    },
    doc = "Rule to run Python tooling (ruff + pyright) on specified targets",
)

# Macro to easily apply both ruff and pyright aspects
def python_tools_check(name, targets):
    """Apply both ruff and pyright aspects to Python targets.

    Args:
        name: Name of the test target
        targets: List of Python targets to check
    """
    python_tools_test(
        name = name,
        targets = targets,
    )
