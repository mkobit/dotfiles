"""
Toolchain type declarations.
"""

# This file contains simplified toolchain type declarations
def declare_toolchain_types():
    """
    Declares all toolchain types that are referenced in the repository.
    
    This is a simplified approach replacing the complex toolchain system.
    """
    native.toolchain_type(
        name = "vim_toolchain_type",
    )
    
    native.toolchain_type(
        name = "neovim_toolchain_type",
    )
    
    native.toolchain_type(
        name = "brew_toolchain_type",
    )