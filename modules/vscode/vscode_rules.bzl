"""
Rules for managing VSCode configurations.
"""

load("//modules/rules:dotfile.bzl", "DotfileInfo")

# Define a provider for VSCode configuration
VscodeConfigInfo = provider(
    doc = "Information about a VSCode configuration",
    fields = {
        "name": "Name of the configuration",
        "settings": "Settings JSON content",
        "platform": "Target platform",
        "variant": "Target variant",
    },
)

# Define a provider for VSCode detection results
VscodeDetectionInfo = provider(
    doc = "Information about VSCode detection",
    fields = {
        "detected": "Whether VSCode is detected",
        "version": "VSCode version if detected",
        "platform": "Platform-specific information",
        "locations": "Paths where VSCode files were found",
    },
)

def _vscode_config_impl(ctx):
    """Implementation of the vscode_config rule."""
    # Get the source file
    src = ctx.file.src
    
    # Determine destination path
    dest = ctx.attr.dest
    if not dest:
        if ctx.attr.is_workspace:
            dest = ".vscode/settings.json"
        else:
            dest = "~/.vscode/settings.json"
    
    # Create a file with installation information
    info_file = ctx.actions.declare_file("%s.info" % ctx.attr.name)
    ctx.actions.write(
        output = info_file,
        content = """
VSCode Config: {name}
Source: {src}
Destination: {dest}
Platform: {platform}
Variant: {variant}
Is Workspace: {is_workspace}
""".format(
            name = ctx.attr.name,
            src = src.path,
            dest = dest,
            platform = ctx.attr.platform,
            variant = ctx.attr.variant,
            is_workspace = ctx.attr.is_workspace,
        ),
    )
    
    # Create a shell script that will install the VSCode config
    install_script = ctx.actions.declare_file("%s.install.sh" % ctx.attr.name)
    ctx.actions.write(
        output = install_script,
        content = """#!/bin/bash
# Installation script for VSCode config {name}
mkdir -p "$(dirname "{dest}")"
cp "{src}" "{dest}"
echo "Installed VSCode config to {dest}"
""".format(
            name = ctx.attr.name,
            src = src.path,
            dest = dest,
        ),
        is_executable = True,
    )
    
    # Return providers
    return [
        DefaultInfo(
            files = depset([src, info_file, install_script]),
            executable = install_script,
            runfiles = ctx.runfiles(files=[src]),
        ),
        DotfileInfo(
            name = ctx.attr.name,
            src = src,
            dest = dest,
            platform = ctx.attr.platform,
            variant = ctx.attr.variant,
        ),
        VscodeConfigInfo(
            name = ctx.attr.name,
            settings = src,
            platform = ctx.attr.platform,
            variant = ctx.attr.variant,
        ),
    ]

# Define the vscode_config rule
vscode_config = rule(
    implementation = _vscode_config_impl,
    attrs = {
        "src": attr.label(
            doc = "Source file for the VSCode configuration",
            allow_single_file = True,
            mandatory = True,
        ),
        "dest": attr.string(
            doc = "Destination path (if different from ~/.vscode/settings.json)",
            default = "",
        ),
        "platform": attr.string(
            doc = "Target platform (e.g., 'linux', 'macos', 'windows')",
            default = "",
        ),
        "variant": attr.string(
            doc = "Target variant (e.g., 'work_laptop', 'personal_desktop')",
            default = "",
        ),
        "is_workspace": attr.bool(
            doc = "Whether this is a workspace-specific settings file",
            default = False,
        ),
    },
    executable = True,
)

def _vscode_detect_impl(ctx):
    """Implementation of the vscode_detect rule."""
    # Create detection output file
    detection_output = ctx.actions.declare_file("%s_detection.json" % ctx.attr.name)
    
    # Create a detection script that writes to the output file
    detect_script = ctx.actions.declare_file("%s.sh" % ctx.attr.name)
    ctx.actions.write(
        output = detect_script,
        content = """#!/bin/bash
# VSCode detection script - outputs results to a JSON file

OUTPUT_FILE="{output_file}"
DETECTION_RESULT="false"
VSCODE_VERSION=""
PLATFORM=""
LOCATIONS="{{}}"

# Define platform-specific paths to check
VSCODE_PATHS=(
    # macOS
    "$HOME/Library/Application Support/Code/User/settings.json"
    # Linux
    "$HOME/.config/Code/User/settings.json"
    # Windows
    "$APPDATA/Code/User/settings.json"
    # WSL
    "/mnt/c/Users/$USER/AppData/Roaming/Code/User/settings.json"
)

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if grep -q Microsoft /proc/version 2>/dev/null; then
        PLATFORM="wsl"
    else
        PLATFORM="linux"
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

# Function to escape JSON string
escape_json() {{
    local str="$1"
    str=$(echo "$str" | sed 's/\\\\/\\\\\\\\/g')
    str=$(echo "$str" | sed 's/"/\\\\"/g')
    str=$(echo "$str" | sed 's/\t/\\\\t/g')
    str=$(echo "$str" | sed 's/\n/\\\\n/g')
    str=$(echo "$str" | sed 's/\r/\\\\r/g')
    echo "$str"
}}

# Check for 'code' command
if command -v code >/dev/null 2>&1; then
    DETECTION_RESULT="true"
    VSCODE_VERSION=$(code --version 2>/dev/null | head -n 1 | tr -d '\\n')
    VSCODE_VERSION=$(escape_json "$VSCODE_VERSION")
fi

# Check for settings.json files
FOUND_LOCATIONS=()
for path in "${{VSCODE_PATHS[@]}}"; do
    expanded_path=$(eval echo "$path")
    if [ -f "$expanded_path" ]; then
        DETECTION_RESULT="true"
        escaped_path=$(escape_json "$expanded_path")
        FOUND_LOCATIONS+=("\\\"$escaped_path\\\"")
    fi
done

# Build locations JSON array
if [ ${{#FOUND_LOCATIONS[@]}} -gt 0 ]; then
    LOCATIONS="["
    for ((i=0; i<${{#FOUND_LOCATIONS[@]}}; i++)); do
        LOCATIONS+="${{FOUND_LOCATIONS[$i]}}"
        if [ $i -lt $((${{#FOUND_LOCATIONS[@]}}-1)) ]; then
            LOCATIONS+=","
        fi
    done
    LOCATIONS+="]"
else
    LOCATIONS="[]"
fi

# Write detection results to JSON file
cat > "$OUTPUT_FILE" << EOF
{{
    "detected": $DETECTION_RESULT,
    "version": "$VSCODE_VERSION",
    "platform": "$PLATFORM",
    "locations": $LOCATIONS
}}
EOF

# Print summary to console
echo "===== VSCode Detection ====="
echo "Platform: $PLATFORM"
echo "VSCode detected: $DETECTION_RESULT"
if [ -n "$VSCODE_VERSION" ]; then
    echo "VSCode version: $VSCODE_VERSION"
fi

echo "Detection results written to $OUTPUT_FILE"
exit 0
""".format(
            output_file = detection_output.path,
        ),
        is_executable = True,
    )
    
    # Create a runner script to execute the detection
    runner_script = ctx.actions.declare_file("%s_runner.sh" % ctx.attr.name)
    ctx.actions.write(
        output = runner_script,
        content = """#!/bin/bash
# Run detection script and create Bazel configuration
{detect_script}

# Extract detection result
DETECTED=$(grep -o '"detected": *[^,]*' {output_file} | awk -F': ' '{{print $2}}')

# Create or update .bazelrc.local based on detection
BAZELRC="{workspace}/.bazelrc.local"

# Create file if it doesn't exist
if [ ! -f "$BAZELRC" ]; then
    echo "# Local Bazel configuration - auto-generated" > "$BAZELRC"
    echo "" >> "$BAZELRC"
fi

# Update or add VSCode detection flag
if grep -q "build --define=HAS_VSCODE=" "$BAZELRC"; then
    sed -i.bak "s/build --define=HAS_VSCODE=[01]/build --define=HAS_VSCODE=$DETECTED/g" "$BAZELRC" && rm -f "$BAZELRC.bak"
    echo "Updated VSCode detection flag in $BAZELRC"
else
    echo "# Tool detection flags" >> "$BAZELRC"
    echo "build --define=HAS_VSCODE=$DETECTED" >> "$BAZELRC"
    echo "Added VSCode detection flag to $BAZELRC"
fi

# Display detection summary from the JSON file
echo ""
echo "Detection summary:"
cat {output_file}
""".format(
            detect_script = detect_script.path,
            output_file = detection_output.path,
            workspace = ctx.workspace_name,
        ),
        is_executable = True,
    )
    
    # Return the runner script as executable and the detection file
    return [
        DefaultInfo(
            files = depset([detection_output]),
            executable = runner_script,
            runfiles = ctx.runfiles(files=[detect_script, detection_output]),
        ),
        OutputGroupInfo(
            detection_json = [detection_output],
        ),
    ]

# Define the vscode_detect rule
vscode_detect = rule(
    implementation = _vscode_detect_impl,
    attrs = {},
    executable = True,
)