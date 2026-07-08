from collections.abc import Mapping
from typing import Any

AGY_INSTALLATION_METHODS = frozenset({"dotfiles.script", "preinstalled", "none", "uninstall"})

MARKER_GATED_INSTALLATION_METHODS = {
    "agy": AGY_INSTALLATION_METHODS,
    "local.bin.btop": frozenset({"github_releases", "homebrew", "none"}),
    "local.bin.opencode": frozenset({"github_releases", "none"}),
    "local.bin.pi": frozenset({"github_releases", "none"}),
    "packages.bubblewrap": frozenset({"apt", "none"}),
    "packages.socat": frozenset({"apt", "none"}),
    "packages.strace": frozenset({"apt", "none"}),
}


def installation_method(data: Mapping[str, Any], feature: str) -> str:
    try:
        return required_installation_method(data, feature)
    except KeyError, TypeError:
        return "none"


def required_installation_method(data: Mapping[str, Any], feature: str) -> str:
    feature_data: Any = data
    for part in feature.split("."):
        if not isinstance(feature_data, Mapping):
            raise KeyError(feature)
        if part not in feature_data:
            raise KeyError(feature)
        feature_data = feature_data.get(part)

    if not isinstance(feature_data, Mapping):
        raise KeyError(feature)

    if "installation_method" not in feature_data:
        raise KeyError(f"{feature}.installation_method")

    method = feature_data["installation_method"]
    if not isinstance(method, str):
        raise TypeError(f"{feature}.installation_method must be a string")

    return method
