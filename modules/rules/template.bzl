"""
Rules for processing template files.
"""

def _template_file_impl(ctx):
    """Implementation of the template_file rule."""
    # Get the template file
    template = ctx.file.template
    
    # Get the variables file if provided
    vars_file = None
    if ctx.file.vars_file:
        vars_file = ctx.file.vars_file
    
    # Create the output file
    output = ctx.outputs.out
    
    # Create a shell script that will process the template
    process_script = ctx.actions.declare_file("%s.process.sh" % ctx.attr.name)
    
    script_content = """#!/bin/bash
# Template processing script for {name}
{template_processor} "{template}" "{output}" "{vars_file}"
""".format(
        name = ctx.attr.name,
        template_processor = ctx.executable._template_processor.path,
        template = template.path,
        output = output.path,
        vars_file = vars_file.path if vars_file else "",
    )
    
    ctx.actions.write(
        output = process_script,
        content = script_content,
        is_executable = True,
    )
    
    # Run the script to generate the output
    inputs = [template]
    if vars_file:
        inputs.append(vars_file)
    
    ctx.actions.run(
        inputs = inputs,
        outputs = [output],
        executable = process_script,
        tools = [ctx.executable._template_processor],
        progress_message = "Processing template %s" % template.path,
    )
    
    # Return providers
    return [
        DefaultInfo(
            files = depset([output]),
        ),
    ]

# Define the template_file rule
template_file = rule(
    implementation = _template_file_impl,
    attrs = {
        "template": attr.label(
            doc = "Template file",
            allow_single_file = True,
            mandatory = True,
        ),
        "vars_file": attr.label(
            doc = "File containing variable definitions",
            allow_single_file = True,
        ),
        "out": attr.output(
            doc = "Output file",
            mandatory = True,
        ),
        "_template_processor": attr.label(
            default = Label("//bin:template_processor"),
            executable = True,
            cfg = "exec",
        ),
    },
)