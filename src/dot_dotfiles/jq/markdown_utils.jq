# Markdown utilities for jq.

# to_markdown_table:
#   Converts an array of JSON objects to a Markdown table, including a header row
#   and separator row.
#
# Input:
#   An array of JSON objects.
#
# Output:
#   A string containing the Markdown table representation of the input.
#
# Example:
#   [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}] | to_markdown_table
#
# Output:
#   | name | age |
#   |------|-----|
#   | Alice | 30 |
#   | Bob | 25 |
def to_markdown_table:
  if type != "array" then
    error("Input must be an array of objects")
  elif length == 0 then
    empty
  else
    (.[0] | keys_unsorted) as $headers |
    # Header row
    "| " + ($headers | join(" | ")) + " |",
    # Separator row
    "| " + ($headers | map("---") | join(" | ")) + " |",
    # Data rows
    (.[] | "| " + ([.[$headers[]]] | map(tostring) | join(" | ")) + " |")
  end;
