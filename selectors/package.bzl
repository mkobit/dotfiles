"""Package management selectors for different platforms."""

load("@platforms//os:macos.bzl", "MACOS_CONSTRAINT")
load("@platforms//os:linux.bzl", "LINUX_CONSTRAINT")
load("@platforms//os:windows.bzl", "WINDOWS_CONSTRAINT")

# Package manager selectors based on OS
PACKAGE_MANAGER = select({
    "@platforms//os:macos": "brew",
    "@platforms//os:linux": "apt",  # Default for Linux, could be refined further
    "@platforms//os:windows": "chocolatey",
    "//conditions:default": "unknown",
})