# jq guide for agents

This document provides guidance on using `jq` within this repository.

## Official documentation

For a comprehensive understanding of `jq`, refer to the [official jq manual](https://jqlang.org/manual/).
For downloads and release information, see the [official jq downloads page](https://jqlang.org/download/).

## jq module system

`jq` supports modules, which allow for the reuse of functions and filters across different `jq` scripts.

### Importing modules

There are two primary ways to use modules:

-   `import MOD as NAME;`: This imports the module `MOD` and assigns its contents to the namespace `NAME`. This is the preferred method as it avoids polluting the global namespace.
-   `include "MOD";`: This includes the module `MOD` directly into the current script, without a namespace. This can be useful for small, self-contained scripts, but should be used with caution to avoid naming conflicts.

### Module search path

`jq` searches for modules in the following locations:

1.  `~/.jq`: A user-level directory for custom modules.
2.  `$ORIGIN/../lib/jq`: A directory relative to the `jq` executable.
3.  Directories specified in the `$JQLIB` environment variable. This is the recommended way to expand the search path for our modules.

## Managing jq modules in this repository

To ensure that our custom `jq` modules are available to all agents and scripts, we will adopt the following convention:

1.  **Module directory**: All custom `jq` modules will be stored in the `src/dot_dotfiles/jq/` directory.
2.  **Environment variable**: The `$JQLIB` environment variable should be updated to include the path to our custom module directory. This will make the modules available to `jq` automatically.
3.  **Naming convention**: Module files should have a `.jq` extension.

This approach allows us to version control our `jq` modules and seamlessly integrate them into the `jq` ecosystem without relying on symlinks.
