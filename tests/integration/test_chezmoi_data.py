import pytest

from chezmoi_test_data import SUPPORTED_INSTALLATION_METHODS, installation_method


def test_installation_method_reads_top_level_feature():
    data = {"agy": {"installation_method": "preinstalled"}}

    assert installation_method(data, "agy") == "preinstalled"


def test_installation_method_defaults_missing_feature_to_none():
    assert installation_method({}, "agy") == "none"


def test_installation_method_defaults_missing_method_to_none():
    assert installation_method({"agy": {}}, "agy") == "none"


def test_supported_installation_methods_include_agy_contract():
    assert SUPPORTED_INSTALLATION_METHODS == frozenset({"dotfiles.script", "preinstalled", "none", "uninstall"})


@pytest.mark.integration
def test_chezmoi_data_contains_agy_installation_method(chezmoi_data):
    assert "agy" in chezmoi_data
    assert installation_method(chezmoi_data, "agy") in SUPPORTED_INSTALLATION_METHODS
