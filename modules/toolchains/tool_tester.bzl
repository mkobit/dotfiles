"""Tool testing rule using Bazel's native genrule approach."""

def _tool_tester_impl(ctx):
    # Create an output file to write tool information
    output = ctx.actions.declare_file(ctx.attr.name + ".info")
    
    # Use a basic shell command that Bazel can execute
    # This will just check if tools exist and write that info to a file
    ctx.actions.run_shell(
        outputs = [output],
        command = """
echo "Tool Detection Report" > "{output}"
echo "===================" >> "{output}"
echo "" >> "{output}"

echo "VIM" >> "{output}"
echo "---" >> "{output}"
if command -v vim &>/dev/null; then
    echo "Available: Yes" >> "{output}"
    echo "Path: $(which vim)" >> "{output}"
    vim --version | head -n 1 >> "{output}"
else
    echo "Available: No" >> "{output}"
fi
echo "" >> "{output}"

echo "NEOVIM" >> "{output}"
echo "------" >> "{output}"
if command -v nvim &>/dev/null; then
    echo "Available: Yes" >> "{output}"
    echo "Path: $(which nvim)" >> "{output}"
    nvim --version | head -n 1 >> "{output}"
else
    echo "Available: No" >> "{output}"
fi
echo "" >> "{output}"

echo "BREW" >> "{output}"
echo "----" >> "{output}"
if command -v brew &>/dev/null; then
    echo "Available: Yes" >> "{output}"
    echo "Path: $(which brew)" >> "{output}"
    echo "Version: $(brew --version | head -n 1)" >> "{output}"
    echo "Prefix: $(brew --prefix)" >> "{output}"
else
    echo "Available: No" >> "{output}"
fi
""".format(output = output.path),
        mnemonic = "ToolInfo",
    )
    
    return [DefaultInfo(files = depset([output]))]

# Define the tool_tester rule
tool_tester = rule(
    implementation = _tool_tester_impl,
    attrs = {},
)