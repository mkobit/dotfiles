#!/usr/bin/env python3
"""
Tests for JSON merge tool functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path

# Import the merge tool functions
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'rules', 'json_merge'))
from json_merge_tool import deep_merge, validate_claude_hooks, _claude_hooks_merge


class TestJsonMergeTool(unittest.TestCase):
    """Test cases for JSON merge tool."""
    
    def test_deep_merge_basic(self):
        """Test basic deep merge functionality."""
        base = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}, "e": 4}
        expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        
        result = deep_merge(base, update)
        self.assertEqual(result, expected)
    
    def test_deep_merge_list_append(self):
        """Test that lists are concatenated."""
        base = {"items": [1, 2]}
        update = {"items": [3, 4]}
        expected = {"items": [1, 2, 3, 4]}
        
        result = deep_merge(base, update)
        self.assertEqual(result, expected)
    
    def test_claude_hooks_merge(self):
        """Test Claude hooks specific merge strategy."""
        base = {
            "hooks": {
                "PreToolUse": {
                    "Bash": "echo 'pre bash'",
                    "Edit": "echo 'pre edit'"
                }
            }
        }
        
        update = {
            "hooks": {
                "PreToolUse": {
                    "Write": "echo 'pre write'"
                },
                "PostToolUse": {
                    "Bash": "echo 'post bash'"
                }
            }
        }
        
        expected = {
            "hooks": {
                "PreToolUse": {
                    "Bash": "echo 'pre bash'",
                    "Edit": "echo 'pre edit'",
                    "Write": "echo 'pre write'"
                },
                "PostToolUse": {
                    "Bash": "echo 'post bash'"
                }
            }
        }
        
        result = _claude_hooks_merge(base, update)
        self.assertEqual(result, expected)
    
    def test_validate_claude_hooks_valid(self):
        """Test validation of valid Claude hooks."""
        valid_hooks = {
            "hooks": {
                "PreToolUse": {
                    "Bash": "echo 'test'"
                },
                "PostToolUse": {
                    "Edit": "echo 'done'"
                }
            }
        }
        
        self.assertTrue(validate_claude_hooks(valid_hooks))
    
    def test_validate_claude_hooks_invalid_structure(self):
        """Test validation rejects invalid structure."""
        invalid_hooks = {
            "not_hooks": {
                "PreToolUse": {
                    "Bash": "echo 'test'"
                }
            }
        }
        
        # Capture stderr to avoid test output noise
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            result = validate_claude_hooks(invalid_hooks)
            self.assertFalse(result)
        finally:
            sys.stderr = old_stderr
    
    def test_validate_claude_hooks_empty_command(self):
        """Test validation rejects empty commands."""
        invalid_hooks = {
            "hooks": {
                "PreToolUse": {
                    "Bash": ""
                }
            }
        }
        
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            result = validate_claude_hooks(invalid_hooks)
            self.assertFalse(result)
        finally:
            sys.stderr = old_stderr
    
    def test_file_operations(self):
        """Test file read/write operations work correctly."""
        test_data = {"test": "value", "nested": {"key": 42}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            from json_merge_tool import load_json_file, write_json_file
            
            # Test load
            loaded = load_json_file(temp_path)
            self.assertEqual(loaded, test_data)
            
            # Test write with deterministic formatting
            output_path = temp_path + ".out"
            write_json_file(test_data, output_path)
            
            # Verify output is properly formatted
            with open(output_path, 'r') as f:
                content = f.read()
                # Should be pretty-printed and end with newline
                self.assertTrue(content.endswith('\n'))
                self.assertIn('  "nested": {', content)  # Check indentation
            
            # Clean up
            os.unlink(output_path)
            
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()