# Interactive jq - Quick & Dirty JSON Filtering

A simple interactive jq tool for real-time JSON filtering with FZF preview. Inspired by [jnv](https://github.com/ynqa/jnv) but implemented as a lightweight shell function.

## Usage

```bash
# Filter a JSON file
ijq data.json

# Filter from stdin
curl -s api.example.com/users | ijq
echo '{"users":[{"name":"Alice","age":30}]}' | ijq
```

## Features

- **Real-time filtering** - See results as you type jq expressions
- **Tmux optimized** - Auto-detects tmux and adjusts preview layout
- **Error handling** - Validates JSON and shows helpful error messages
- **FZF integration** - Uses your existing FZF styling
- **Cross-platform** - Works with files or stdin

## Key Bindings

- `Enter` - Output the filtered result
- `Ctrl+/` - Toggle preview window position
- `Ctrl+R` - Reset/clear current filter
- `Ctrl+C` - Exit without output

## Examples

Start `ijq data.json` and try these filters:

```bash
.                              # Show entire JSON
.users[]                       # All users
.users[] | select(.active)     # Filter active users
.users[].name                  # Extract all names
.users[] | {name, email}       # Select specific fields
.metadata.tags[]               # Get array elements
```

## Environment Optimization

### Terminal
- Large preview window (60% height)
- Full border styling

### Tmux
- Side preview (50% width) to preserve space
- Rounded borders for better appearance
- Automatic detection and adjustment

## Dependencies

- `fzf` - Fuzzy finder ([install](https://github.com/junegunn/fzf#installation))
- `jq` - JSON processor ([install](https://stedolan.github.io/jq/download/))

Missing dependencies show helpful installation hints.

## Quick Start

1. Ensure `fzf` and `jq` are installed
2. Reload your shell to get the `ijq` function
3. Try: `echo '{"hello":"world","items":[1,2,3]}' | ijq`
4. Type: `.items[]` and see real-time results!

Perfect for exploring API responses, config files, and any JSON data without running jq multiple times.
