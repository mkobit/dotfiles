"""Tests for the SSH configuration module."""

load("@bazel_skylib//lib:unittest.bzl", "analysistest", "asserts")
load("//modules/ssh:ssh_rules.bzl", "ssh_config", "ssh_config_generator")

def _ssh_config_test_impl(ctx):
    env = analysistest.begin(ctx)
    
    # Get the target under test
    target = analysistest.target_under_test(env)
    
    # Check that the target produced exactly one output file
    asserts.equals(env, 1, len(target[DefaultInfo].files.to_list()))
    
    # Test passes if we get here
    return analysistest.end(env)

ssh_config_test = analysistest.make(_ssh_config_test_impl)

def _test_basic_ssh_config():
    """Test that basic SSH config generation works."""
    
    # Define a test config
    ssh_config(
        name = "test_config",
        global_options = {
            "AddKeysToAgent": "yes",
            "HashKnownHosts": "yes",
        },
        hosts = {
            "test.example.com.User": "testuser",
            "test.example.com.IdentityFile": "~/.ssh/id_test",
        },
        testonly = True,
    )
    
    # Generate a config file from it
    ssh_config_generator(
        name = "test_ssh_config",
        config = ":test_config",
        testonly = True,
    )
    
    # Test the generator
    ssh_config_test(
        name = "ssh_config_generation_test",
        target_under_test = ":test_ssh_config",
    )

def ssh_config_test_suite():
    """Create the test suite for SSH config."""
    _test_basic_ssh_config()