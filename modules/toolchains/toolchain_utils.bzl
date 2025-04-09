"""Utility functions for accessing toolchains."""

def get_tool_path(ctx, toolchain_type, provider_field = None, tool_name = None):
    """Get the path to a tool from a toolchain.
    
    Args:
        ctx: The rule context
        toolchain_type: The toolchain type, e.g. "//modules/toolchains:vim_toolchain_type"
        provider_field: The field in the toolchain info to access, e.g. "vim_info"
        tool_name: The name of the tool for error messages
        
    Returns:
        The path to the tool, or None if not available
    """
    toolchain = None
    if toolchain_type in ctx.toolchains:
        toolchain = ctx.toolchains[toolchain_type]
    else:
        # Toolchain not available
        return None
        
    if toolchain and provider_field and hasattr(toolchain, provider_field):
        provider = getattr(toolchain, provider_field)
        if hasattr(provider, "path"):
            return provider.path
    
    # If we have tool_info, use that as a fallback
    if toolchain and hasattr(toolchain, "tool_info"):
        return toolchain.tool_info.path
        
    return None
    
def is_tool_available(ctx, toolchain_type):
    """Check if a tool is available from a toolchain.
    
    Args:
        ctx: The rule context
        toolchain_type: The toolchain type
        
    Returns:
        True if the tool is available, False otherwise
    """
    path = get_tool_path(ctx, toolchain_type)
    return path != None and path != ""
    
def vim_path(ctx):
    """Get the path to the vim executable."""
    return get_tool_path(ctx, "//modules/toolchains:vim_toolchain_type", "vim_info", "vim")
    
def neovim_path(ctx):
    """Get the path to the neovim executable."""
    return get_tool_path(ctx, "//modules/toolchains:neovim_toolchain_type", "neovim_info", "neovim")
    
def brew_path(ctx):
    """Get the path to the brew executable."""
    return get_tool_path(ctx, "//modules/toolchains:brew_toolchain_type", "brew_info", "brew")