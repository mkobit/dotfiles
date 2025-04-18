"""Rules for managing jq modules and toolchain."""

# Define the JqModuleInfo provider to make module data strongly typed
JqModuleInfo = provider(
    doc = "Information about jq module configuration",
    fields = {
        "name": "Name of the module",
        "source": "Source path or label to the module",
        "imports": "List of other modules to import",
        "search_paths": "List of paths to search for modules",
        "raw_content": "Raw module content if specified directly",
    },
)

def _jq_module_impl(ctx):
    """Implementation of jq_module rule."""
    
    # Process imports to build dependencies
    imports = []
    search_paths = list(ctx.attr.search_paths)
    
    # Collect imports from dependencies
    for dep in ctx.attr.imports:
        if JqModuleInfo in dep:
            dep_info = dep[JqModuleInfo]
            imports.append(dep_info.name)
            # Add search paths from dependencies
            for path in dep_info.search_paths:
                if path not in search_paths:
                    search_paths.append(path)
    
    # Determine source - either from file or raw content
    source = None
    raw_content = ctx.attr.content
    
    if ctx.file.src:
        source = ctx.file.src
    
    # Generate output file
    output_file = ctx.actions.declare_file(ctx.attr.name + ".jq")
    
    # If we have a source file, copy it to the output
    if source:
        ctx.actions.run_shell(
            inputs = [source],
            outputs = [output_file],
            command = "cp {} {}".format(source.path, output_file.path),
        )
    elif raw_content:
        # If we have raw content, write it to the output
        ctx.actions.write(
            output = output_file,
            content = raw_content,
        )
    else:
        # If neither source nor content, create an empty file
        ctx.actions.write(
            output = output_file,
            content = "# Empty jq module: {}\n".format(ctx.attr.name),
        )
    
    # Create runfiles with the module and any imports
    runfiles = ctx.runfiles(files = [output_file])
    
    # Add transitive imports
    for dep in ctx.attr.imports:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)
    
    # Create the provider
    module_info = JqModuleInfo(
        name = ctx.attr.name,
        source = source,
        imports = imports,
        search_paths = search_paths,
        raw_content = raw_content,
    )
    
    return [
        module_info,
        DefaultInfo(
            files = depset([output_file]),
            runfiles = runfiles,
        ),
    ]

jq_module = rule(
    implementation = _jq_module_impl,
    attrs = {
        "src": attr.label(
            allow_single_file = [".jq"],
            doc = "Source file for the jq module",
        ),
        "content": attr.string(
            doc = "Raw content for the jq module (alternative to src)",
        ),
        "imports": attr.label_list(
            doc = "Other jq modules to import",
            providers = [JqModuleInfo],
            default = [],
        ),
        "search_paths": attr.string_list(
            doc = "Additional paths to search for modules",
            default = [],
        ),
    },
)

def _jq_library_impl(ctx):
    """Implementation of jq_library rule to bundle multiple jq modules."""
    
    # Collect all modules
    modules = []
    all_files = []
    all_search_paths = list(ctx.attr.search_paths)
    
    # Process all module dependencies
    for dep in ctx.attr.modules:
        if JqModuleInfo in dep:
            mod_info = dep[JqModuleInfo]
            modules.append(mod_info)
            
            # Collect search paths
            for path in mod_info.search_paths:
                if path not in all_search_paths:
                    all_search_paths.append(path)
        
        # Collect files from DefaultInfo
        if DefaultInfo in dep:
            all_files.extend(dep[DefaultInfo].files.to_list())
    
    # Create aggregated runfiles
    runfiles = ctx.runfiles(files = all_files)
    for dep in ctx.attr.modules:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)
    
    # Return a DefaultInfo with all the files
    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = runfiles,
        ),
    ]

jq_library = rule(
    implementation = _jq_library_impl,
    attrs = {
        "modules": attr.label_list(
            doc = "jq modules to include in this library",
            providers = [JqModuleInfo],
            default = [],
        ),
        "search_paths": attr.string_list(
            doc = "Additional paths to search for modules",
            default = [],
        ),
    },
)

def _jq_test_impl(ctx):
    """Implementation of jq_test rule to test jq modules."""
    
    # Create the test script
    test_script = ctx.actions.declare_file(ctx.attr.name + ".test.sh")
    
    # Create runfiles with the test script and all dependencies
    runfiles = ctx.runfiles(files = [test_script])
    
    # Add transitive dependencies from the module
    if DefaultInfo in ctx.attr.module:
        runfiles = runfiles.merge(ctx.attr.module[DefaultInfo].default_runfiles)
    
    # Get the module info
    module_info = ctx.attr.module[JqModuleInfo] if JqModuleInfo in ctx.attr.module else None
    module_path = ""
    search_paths = []
    
    # Build search paths and other args
    if module_info:
        search_paths = module_info.search_paths
    
    # Build the module file path
    module_files = ctx.attr.module[DefaultInfo].files.to_list() if DefaultInfo in ctx.attr.module else []
    if module_files:
        module_path = module_files[0].short_path
    
    # Build the jq search path argument
    l_args = ""
    for path in search_paths:
        if path:
            l_args += ' -L "{}"'.format(path)
    
    # Get the test input and expected output
    test_input = ctx.attr.input_data
    expected_output = ctx.attr.expected_output
    
    # Create the test script content
    script_content = """#!/bin/bash
set -euo pipefail

echo "=== jq Module Test: {} ==="

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found"
    exit 1
fi

# Set up paths
MODULE_PATH="{}"
if [ ! -f "$MODULE_PATH" ]; then
    echo "ERROR: Module file not found: $MODULE_PATH"
    exit 1
fi

# Run the test
INPUT='{}'
EXPECTED='{}'
SEARCH_PATHS="{}"

echo "Running jq with module..."
RESULT=$(echo "$INPUT" | jq $SEARCH_PATHS -f "$MODULE_PATH" 2>&1)
echo "Result: $RESULT"
echo "Expected: $EXPECTED"

if [ "$RESULT" = "$EXPECTED" ]; then
    echo "TEST PASSED: Output matches expected value"
    exit 0
else
    echo "TEST FAILED: Output does not match expected value"
    exit 1
fi
""".format(
        ctx.attr.name,
        module_path,
        test_input,
        expected_output,
        l_args,
    )
    
    # Write the test script
    ctx.actions.write(
        output = test_script,
        content = script_content,
        is_executable = True,
    )
    
    return [
        DefaultInfo(
            executable = test_script,
            runfiles = runfiles,
        ),
    ]

jq_test = rule(
    implementation = _jq_test_impl,
    attrs = {
        "module": attr.label(
            doc = "jq module to test",
            providers = [JqModuleInfo],
            mandatory = True,
        ),
        "input_data": attr.string(
            doc = "Input JSON data for the test",
            default = "{}",
        ),
        "expected_output": attr.string(
            doc = "Expected output from jq",
            default = "{}",
        ),
    },
    test = True,
)