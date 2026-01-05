#!/usr/bin/env bash
# Test script for markdown_utils.jq module

set -euo pipefail

if ! command -v jq &> /dev/null; then
    echo "jq not installed, skipping tests"
    exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Testing markdown_utils.jq..."

# Test 1: Basic table conversion
echo -n "Test 1 (basic table): "
output=$(echo '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]' | \
    jq -r -L "$SCRIPT_DIR" 'include "markdown_utils"; to_markdown_table')
expected="| name | age |
| --- | --- |
| Alice | 30 |
| Bob | 25 |"
if [[ "$output" == "$expected" ]]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "Expected:"
    echo "$expected"
    echo "Got:"
    echo "$output"
    exit 1
fi

# Test 2: Single object
echo -n "Test 2 (single object): "
output=$(echo '[{"x": 1}]' | jq -r -L "$SCRIPT_DIR" 'include "markdown_utils"; to_markdown_table')
expected="| x |
| --- |
| 1 |"
if [[ "$output" == "$expected" ]]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Test 3: Empty array
echo -n "Test 3 (empty array): "
output=$(echo '[]' | jq -r -L "$SCRIPT_DIR" 'include "markdown_utils"; to_markdown_table')
if [[ -z "$output" ]]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

# Test 4: Multiple data types
echo -n "Test 4 (multiple types): "
output=$(echo '[{"text": "hello", "num": 42, "bool": true}]' | \
    jq -r -L "$SCRIPT_DIR" 'include "markdown_utils"; to_markdown_table')
expected="| text | num | bool |
| --- | --- | --- |
| hello | 42 | true |"
if [[ "$output" == "$expected" ]]; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    exit 1
fi

echo ""
echo "All tests passed!"
