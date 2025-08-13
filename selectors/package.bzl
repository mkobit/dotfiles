"""Package management selectors for different platforms."""

PACKAGE_MANAGER = select({
    "@platforms//os:macos": "brew",
    "@platforms//os:linux": "apt",
    "//conditions:default": "unknown",
})
