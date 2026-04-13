#!/bin/bash
set -e
uv run ruff check .
uv run ruff format --check .
