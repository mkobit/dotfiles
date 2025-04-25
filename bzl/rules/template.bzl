"""
Rules for processing template files using Bazel-native mechanisms.
"""

def template_file(name, template, out, vars_files = None, vars_file = None, substitutions = None, **kwargs):
    """Macro to create a template processing genrule.
    
    Args:
        name: The name of the rule
        template: The template file
        out: The output file
        vars_files: List of properties files with variables
        vars_file: Single properties file with variables (mutually exclusive with vars_files)
        substitutions: Direct key-value substitutions as a dict
        **kwargs: Additional keyword arguments passed to the genrule
    """
    if vars_files and vars_file:
        fail("Cannot specify both vars_files and vars_file. Choose one.")
    
    # Use vars_file as a single-item list if provided
    if vars_file:
        vars_files = [vars_file]
    elif not vars_files:
        vars_files = []
    
    # Create the sed commands for variable substitution
    sed_commands = []
    for i, var_file in enumerate(vars_files):
        # For each properties file, process its key-value pairs
        sed_commands.append("echo 'Processing variables from $(location {})'" .format(var_file))
        sed_commands.append("while IFS='=' read -r key value; do")
        sed_commands.append("  # Skip empty lines and comments")
        sed_commands.append("  [[ \"$$key\" =~ ^[[:space:]]*$$ || \"$$key\" =~ ^[[:space:]]*# ]] && continue")
        sed_commands.append("  # Trim whitespace from key")
        sed_commands.append("  key=$$(echo \"$$key\" | tr -d ' ')")
        sed_commands.append("  # Replace template variables")
        sed_commands.append("  sed -i.bak \"s|{{$$key}}|$$value|g\" temp_file")
        sed_commands.append("done < $(location {})".format(var_file))
    
    # Add direct substitutions if provided
    if substitutions:
        for key, value in substitutions.items():
            sed_commands.append("# Direct substitution for {}".format(key))
            sed_commands.append("sed -i.bak \"s|{}|{}|g\" temp_file".format(key, value))
    
    # Create the genrule (without the problematic tmux version processing)
    native.genrule(
        name = name,
        srcs = [template] + (vars_files or []),
        outs = [out],
        cmd = """
        # Create a temporary file
        cp $(location {template}) temp_file
        
        # Process each properties file and direct substitutions
        {sed_commands}
        
        # Move to the output location
        cp temp_file $@
        """.format(
            template = template,
            sed_commands = "\n        ".join(sed_commands),
        ),
        **kwargs
    )