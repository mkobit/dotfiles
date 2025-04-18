"""
Simple genrule-based dotfile utilities.
This replaces the more complex dotfile rule that uses shell scripts.
"""

def simple_dotfile_output(name, src, dest = None):
    """Returns the output file name for a simple dotfile target.
    Args:
        name: The name of the rule.
        src: The source file.
        dest: Optional destination path.
    Returns:
        Output file name that will contain the destination path.
    """
    return name + "_path.txt"

def simple_dotfile(name, src, dest = None, **kwargs):
    """A simplified dotfile rule that just outputs the path.
    
    This rule doesn't create any symlinks or shell scripts.
    Instead, it produces an output file showing the location of the 
    generated configuration, so it can be referenced directly.
    
    Args:
        name: The name of the rule.
        src: The source file to use as config.
        dest: Optional destination path where this would be installed.
        **kwargs: Additional keyword arguments passed to genrule.
    """
    if not dest:
        dest = "~/.{}".format(name)
        
    output_file = simple_dotfile_output(name, src, dest)
    
    native.genrule(
        name = name,
        srcs = [src],
        outs = [output_file],
        cmd = """
echo "# Dotfile configuration for {name}" > $@
echo "Source: $(location {src})" >> $@
echo "Destination: {dest}" >> $@
echo "" >> $@
echo "To use this configuration, copy the content or reference directly from:" >> $@
echo "$(location {src})" >> $@
""".format(
            name = name,
            src = src,
            dest = dest,
        ),
        **kwargs
    )
    
    # Also create a print target
    native.genrule(
        name = name + "_print",
        srcs = [src],
        outs = [name + "_print.sh"],
        cmd = """
echo '#!/bin/bash' > $@
echo 'echo "Config file for {name} is available at:"' >> $@
echo 'echo "$$PWD/$(location {src})"' >> $@
echo 'echo "It would typically be installed at: {dest}"' >> $@
chmod +x $@
""".format(
            name = name,
            src = src,
            dest = dest,
        ),
        executable = True,
        **kwargs
    )

def simple_dotfile_group(name, deps, **kwargs):
    """A simplified dotfile group that just aggregates outputs.
    
    Args:
        name: The name of the rule.
        deps: List of simple_dotfile targets to include.
        **kwargs: Additional keyword arguments passed to genrule.
    """
    # Create an aggregated output listing all dotfiles
    native.genrule(
        name = name,
        srcs = deps,
        outs = [name + "_manifest.txt"],
        cmd = """
echo "# Dotfile manifest for {name}" > $@
echo "" >> $@
for src in $(SRCS); do
  cat $$src >> $@
  echo "-------------------------------------------" >> $@
done
echo "Generated: $$(date)" >> $@
""".format(name = name),
        **kwargs
    )
    
    # Create a print target
    native.genrule(
        name = name + "_print",
        srcs = deps,
        outs = [name + "_print.sh"],
        cmd = """
echo '#!/bin/bash' > $@
echo 'echo "Dotfile group {name} contains:"' >> $@
echo 'for file in "$@"; do' >> $@
echo '  echo "- $$file"' >> $@
echo 'done' >> $@
chmod +x $@
""".format(name = name),
        executable = True,
        **kwargs
    )