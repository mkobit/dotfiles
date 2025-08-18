"""
Public API for dependency management rules.
"""

load("//rules/deps/private:binary_artifact.bzl", _binary_artifact_dependency = "binary_artifact_dependency")
load("//rules/deps/private:git_repository.bzl", _git_repository_dependency = "git_repository_dependency")

# Re-export the rules
git_repository_dependency = _git_repository_dependency
binary_artifact_dependency = _binary_artifact_dependency
