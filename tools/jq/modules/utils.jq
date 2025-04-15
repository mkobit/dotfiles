# Utility functions for jq
# This is an example module file that will be available in the modules directory

# String utilities
def trim: sub("^\\s+"; "") | sub("\\s+$"; "");
def uppercase: ascii_upcase;
def lowercase: ascii_downcase;
def capitalize: .[0:1] | uppercase + .[1:] | lowercase;

# Array operations
def sum_array: reduce .[] as $item (0; . + $item);
def product_array: reduce .[] as $item (1; . + $item);
def mean: add / length;
def median: 
  sort | 
  if length == 0 then null
  elif length % 2 == 0 then
    .[(length/2)-1, length/2] | add/2
  else
    .[length/2]
  end;

# Object operations
def pick(paths):
  reduce paths[] as $path ({};
    . + { ($path): (. | getpath($path | split("."))) }
  );

# Date formatting
def iso_date: strftime("%Y-%m-%dT%H:%M:%SZ");
def friendly_date: strftime("%B %d, %Y");

# Filtering
def filter_by_value(key; value): map(select(.[key] == value));