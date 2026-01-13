# Obsidian Local API Tool

A Python CLI tool and library for interacting with the [Obsidian Local REST API](https://coddingtonbear.github.io/obsidian-local-rest-api/).

## Installation

This tool is managed by `chezmoi` and `bazel`. It is typically installed to `~/.local/bin/tools/obsidian-local-api`.

## Usage

### Authentication

The tool requires an authentication token to communicate with the Obsidian Local REST API. The token is resolved in the following order:

1.  **Command-line argument:** `--token <your-token>`
2.  **Token file argument:** `--token-file /path/to/token-file`
3.  **Environment file:** `OBSIDIAN_API_TOKEN` variable in a `.env` file in the current directory.
4.  **XDG Config:** `~/.config/obsidian-local-api/token`

### Commands

The CLI supports the following commands:

-   `active`: Get the currently active file in Obsidian.
-   `commands`: List available commands.
-   `delete <path>`: Delete a file from the vault.
-   `list [folder]`: List files in the vault (defaults to root).
-   `read <path>`: Read the content of a file.
-   `run-command <command_id>`: Run a specific Obsidian command.
-   `search <query>`: Search the vault.
-   `write <path> <content>`: Write content to a file.

### Examples

**List files in the root directory:**

```bash
obsidian-local-api list
```

**Read a specific note:**

```bash
obsidian-local-api read "Daily Notes/2023-10-27.md"
```

**Get the active file:**

```bash
obsidian-local-api active
```

**Using a specific token:**

```bash
obsidian-local-api --token "my-secret-token" active
```
