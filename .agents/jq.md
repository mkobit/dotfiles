# jq Guide for Agents

This document provides guidance on using `jq` within this repository, including how to manage and use custom modules.

## Official Documentation

For a comprehensive understanding of `jq`, refer to the [official jq manual](https://jqlang.org/manual/).

## `jq` Module System

`jq` supports modules, which allow for the reuse of functions and filters across different `jq` scripts. This is essential for maintaining clean and maintainable code.

### Importing Modules

There are two primary ways to use modules:

-   `import MOD as NAME;`: This imports the module `MOD` and assigns its contents to the namespace `NAME`. This is the preferred method as it avoids polluting the global namespace.
-   `include "MOD";`: This includes the module `MOD` directly into the current script, without a namespace. This can be useful for small, self-contained scripts, but should be used with caution to avoid naming conflicts.

### Module Search Path

`jq` searches for modules in the following locations:

1.  `~/.jq`: A user-level directory for custom modules.
2.  `$ORIGIN/../lib/jq`: A directory relative to the `jq` executable.
3.  Directories specified in the `$JQLIB` environment variable.

## Managing `jq` Modules in this Repository

To ensure that our custom `jq` modules are available to all agents and scripts, we will adopt the following convention:

1.  **Module Directory**: All custom `jq` modules will be stored in the `src/dot_jq/` directory.
2.  **Symlinking**: During the `chezmoi apply` process, the `src/dot_jq` directory will be symlinked to `~/.jq`. This will make all modules within `src/dot_jq` automatically available to `jq`.
3.  **Naming Convention**: Module files should have a `.jq` extension.

This approach allows us to version control our `jq` modules and seamlessly integrate them into the `jq` ecosystem.

## Example Module: Object to CSV

As an example, we will create a module for converting JSON objects to CSV format. This module will be located at `src/dot_jq/obj2csv.jq` and will contain a function called `to_csv`.
