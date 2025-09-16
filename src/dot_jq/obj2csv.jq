# Module to convert an array of JSON objects to CSV format.

# to_csv:
#   Converts an array of JSON objects to CSV format, including a header row.
#
# Input:
#   An array of JSON objects.
#
# Output:
#   A string containing the CSV representation of the input.
#
# Example:
#   [{"a": 1, "b": 2}, {"a": 3, "b": 4}] | to_csv
#
# Output:
#   "a","b"
#   1,2
#   3,4
def to_csv:
  if length == 0 then
    empty
  else
    (.[0] | keys_unsorted) as $headers |
    $headers,
    (.[] | [.[$headers[]]]) |
    @csv
  end;
