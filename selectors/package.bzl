"""Package management selectors for different platforms."""

load("@platforms//os:macos.bzl", "MACOS_CONSTRAINT")
load("@platforms//os:linux.bzl", "LINUX_CONSTRAINT")
load("@platforms//os:windows.bzl", "WINDOWS_CONSTRAINT")

PACKAGE_MANAGER = select({
    "@platforms//os:macos": "brew",
    "@platforms//os:linux": "apt",
    "@platforms//os:windows": "chocolatey",
    "//conditions:default": "unknown",
})
