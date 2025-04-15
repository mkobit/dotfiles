# Advanced jq functions that import the utils module
# This demonstrates how modules can import each other

import "utils" as utils;

# Process JSON data using imported functions
def process_strings:
  if type == "object" then
    with_entries(.value |= if type == "string" then utils::trim | utils::capitalize else . end)
  elif type == "array" then
    map(if type == "string" then utils::trim | utils::capitalize else . end)
  elif type == "string" then
    utils::trim | utils::capitalize
  else
    .
  end;

# Calculate statistics on arrays
def statistics:
  {
    sum: utils::sum_array,
    mean: utils::mean,
    median: utils::median,
    count: length,
    min: min,
    max: max
  };

# Format dates in multiple formats
def format_dates:
  {
    iso: utils::iso_date,
    friendly: utils::friendly_date,
    year: strftime("%Y"),
    month: strftime("%m"),
    day: strftime("%d")
  };