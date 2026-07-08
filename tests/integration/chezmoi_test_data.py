from collections.abc import Mapping
from typing import Any

SUPPORTED_INSTALLATION_METHODS = frozenset({"dotfiles.script", "preinstalled", "none", "uninstall"})


def installation_method(data: Mapping[str, Any], feature: str) -> str:
    feature_data: Any = data
    for part in feature.split("."):
        if not isinstance(feature_data, Mapping):
            return "none"
        feature_data = feature_data.get(part)

    if not isinstance(feature_data, Mapping):
        return "none"

    method = feature_data.get("installation_method", "none")
    if not isinstance(method, str):
        return "none"

    return method
