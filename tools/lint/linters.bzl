"""
Linting aspects for the repository.
"""

load("@aspect_rules_lint//lint:ruff.bzl", "lint_ruff_aspect")
load("@aspect_rules_lint//lint:ty.bzl", "lint_ty_aspect")

# Define Ruff aspect
ruff = lint_ruff_aspect(
    binary = "@@//tools/lint:ruff",
    configs = [Label("//:pyproject.toml")],
)

# Define Ty aspect using rules_lint
ty = lint_ty_aspect(
    binary = "@@//tools/python:ty",
    config = Label("//:pyproject.toml"),
)
