"""
Helper functions for selecting configuration based on platform and variant.
"""

# Import bazel_skylib select utilities for combining select statements
load("@bazel_skylib//lib:selects.bzl", "selects")

def select_platform(macos_value = None, linux_value = None, windows_value = None, wsl_value = None, default = None):
    """
    Creates a select() statement for platform-specific values.
    
    Args:
        macos_value: Value to use on macOS
        linux_value: Value to use on Linux (excluding WSL)
        windows_value: Value to use on Windows
        wsl_value: Value to use on WSL
        default: Default value if none of the platforms match
        
    Returns:
        A select() statement for platform-specific configuration
    """
    selection = {}
    
    if macos_value != None:
        selection["//selectors:macos"] = macos_value
    
    if linux_value != None:
        selection["//selectors:linux"] = linux_value
    
    if windows_value != None:
        selection["//selectors:windows"] = windows_value
        
    if wsl_value != None:
        selection["//selectors:wsl"] = wsl_value
        
    if default != None:
        selection["//conditions:default"] = default
    elif selection:
        # If no default provided, use the first value as default
        first_key = list(selection.keys())[0]
        selection["//conditions:default"] = selection[first_key]
        
    return select(selection)

def select_variant(personal_value = None, work_value = None, minimal_value = None, default = None):
    """
    Creates a select() statement for variant-specific values.
    
    Args:
        personal_value: Value to use for personal variant
        work_value: Value to use for work variant
        minimal_value: Value to use for minimal variant
        default: Default value if none of the variants match
        
    Returns:
        A select() statement for variant-specific configuration
    """
    selection = {}
    
    if personal_value != None:
        selection["//config:is_personal"] = personal_value
    
    if work_value != None:
        selection["//config:is_work"] = work_value
    
    if minimal_value != None:
        selection["//config:is_minimal"] = minimal_value
        
    if default != None:
        selection["//conditions:default"] = default
    elif selection:
        # If no default provided, use the first value as default
        first_key = list(selection.keys())[0]
        selection["//conditions:default"] = selection[first_key]
        
    return select(selection)

def select_platform_variant(
        macos_personal = None, macos_work = None, macos_minimal = None,
        linux_personal = None, linux_work = None, linux_minimal = None, 
        windows_personal = None, windows_work = None, windows_minimal = None,
        default = None):
    """
    Creates a select() statement for platform+variant combinations.
    
    Args:
        macos_personal: Value to use for macOS + personal variant
        macos_work: Value to use for macOS + work variant
        macos_minimal: Value to use for macOS + minimal variant
        linux_personal: Value to use for Linux + personal variant
        linux_work: Value to use for Linux + work variant
        linux_minimal: Value to use for Linux + minimal variant
        windows_personal: Value to use for Windows + personal variant
        windows_work: Value to use for Windows + work variant  
        windows_minimal: Value to use for Windows + minimal variant
        default: Default value if none of the combinations match
        
    Returns:
        A select() statement for platform+variant combinations
    """
    selection = {}
    
    # macOS combinations
    if macos_personal != None:
        selection["//config:macos_personal"] = macos_personal
    if macos_work != None:
        selection["//config:macos_work"] = macos_work
    if macos_minimal != None:
        selection["//config:macos_minimal"] = macos_minimal
    
    # Linux combinations
    if linux_personal != None:
        selection["//config:linux_personal"] = linux_personal
    if linux_work != None:
        selection["//config:linux_work"] = linux_work
    if linux_minimal != None:
        selection["//config:linux_minimal"] = linux_minimal
    
    # Windows combinations
    if windows_personal != None:
        selection["//config:windows_personal"] = windows_personal
    if windows_work != None:
        selection["//config:windows_work"] = windows_work
    if windows_minimal != None:
        selection["//config:windows_minimal"] = windows_minimal
    
    if default != None:
        selection["//conditions:default"] = default
    elif selection:
        # If no default provided, use the first value as default
        first_key = list(selection.keys())[0]
        selection["//conditions:default"] = selection[first_key]
        
    return select(selection)