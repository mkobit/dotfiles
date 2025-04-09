"""Cross-platform toolchain tests using Bazel's Python test framework."""

import os
import subprocess
import unittest
import sys

class ToolchainTest(unittest.TestCase):
    """Tests for toolchain availability."""
    
    def _check_tool_exists(self, tool_name):
        """Check if a tool exists in the PATH."""
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            if os.path.exists(os.path.join(path_dir, tool_name)):
                return True
        return False
    
    def _get_tool_version(self, tool_name, version_args=None):
        """Get the version of a tool."""
        if not self._check_tool_exists(tool_name):
            return None
            
        if version_args is None:
            version_args = ["--version"]
            
        try:
            result = subprocess.run(
                [tool_name] + version_args,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None
    
    def test_vim_availability(self):
        """Test vim availability (but don't fail if not available)."""
        vim_exists = self._check_tool_exists("vim")
        if vim_exists:
            version = self._get_tool_version("vim")
            self.assertIsNotNone(version, "Vim should return a version string")
            print(f"Vim version: {version.splitlines()[0]}")
        else:
            print("Vim not available")
    
    def test_neovim_availability(self):
        """Test neovim availability (but don't fail if not available)."""
        nvim_exists = self._check_tool_exists("nvim")
        if nvim_exists:
            version = self._get_tool_version("nvim")
            self.assertIsNotNone(version, "Neovim should return a version string")
            print(f"Neovim version: {version.splitlines()[0]}")
        else:
            print("Neovim not available")
    
    def test_brew_availability(self):
        """Test brew availability (but don't fail if not available)."""
        brew_exists = self._check_tool_exists("brew")
        if brew_exists:
            version = self._get_tool_version("brew")
            if version:
                print(f"Brew version: {version.splitlines()[0]}")
            else:
                print("Brew version could not be determined")
            
            # Test brew prefix
            try:
                prefix = subprocess.run(
                    ["brew", "--prefix"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if prefix.returncode == 0:
                    print(f"Brew prefix: {prefix.stdout.strip()}")
            except Exception:
                pass
        else:
            print("Brew not available")

if __name__ == "__main__":
    unittest.main()