= jq Module Configuration
:version: %%VERSION%%

== Overview

This module provides toolchain support and Bazel integration for jq modules.
jq is a lightweight, flexible command-line JSON processor.

== Module System

jq has a library/module system. Modules are files whose names end in `.jq`.

=== Search Path Rules

Modules are searched for in this order:

1. Paths provided with the `-L` flag 
2. Default search paths:
   * `~/.jq`
   * `$ORIGIN/../lib/jq` (directory where jq executable is installed)
   * `$ORIGIN/../lib`

For paths starting with `~/`, the user's home directory is substituted for `~`.

For paths starting with `$ORIGIN/`, the directory where the jq executable is located is substituted for `$ORIGIN`.

For paths starting with `./` or paths that are `.`, the path of the including file is substituted for `.`.

=== Module Resolution

A dependency with relative path `foo/bar` would be searched for in:
* `foo/bar.jq` 
* `foo/bar/bar.jq`

This allows modules to be placed in a directory along with other files, or as single-file modules.

== Usage in Bazel

=== Creating a jq module

[source,python]
----
load("//modules/jq:jq_rules.bzl", "jq_module")

jq_module(
    name = "my_module",
    content = """
def say_hello: "Hello from jq!";
def add(a; b): a + b;
""",
)
----

=== Creating a jq module from a file

[source,python]
----
jq_module(
    name = "my_module",
    src = "my_module.jq",
)
----

=== Importing other modules

[source,python]
----
jq_module(
    name = "advanced_module",
    content = """
import "my_module" as basic;

def process_data:
  . | basic::add(.; 42);
""",
    imports = [":my_module"],
    search_paths = ["~/.jq", "$(pwd)/tools/jq/modules"],
)
----

=== Testing a jq module

[source,python]
----
load("//modules/jq:jq_rules.bzl", "jq_test")

jq_test(
    name = "my_module_test",
    module = ":my_module", 
    input_data = '{"value": 40}',
    expected_output = '82',
)
----

=== Creating a jq library

[source,python]
----
load("//modules/jq:jq_rules.bzl", "jq_library")

jq_library(
    name = "my_jq_library",
    modules = [
        ":my_module",
        ":advanced_module",
    ],
    search_paths = ["~/.jq"],
)
----

== Installation

Run the following to install jq modules to your `~/.jq` directory:

[source,bash]
----
bazel run //tools/jq:install_modules
----

== Toolchain Configuration

The jq toolchain automatically detects the installed jq version and capabilities:

[source,bash]
----
# Run the integration test to verify jq installation
bazel test //tools/jq:system_integration_test
----