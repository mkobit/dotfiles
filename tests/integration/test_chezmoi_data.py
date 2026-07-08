import pytest
from chezmoi_test_data import (
    AGY_INSTALLATION_METHODS,
    MARKER_GATED_INSTALLATION_METHODS,
    installation_method,
    required_installation_method,
)


def test_installation_method_reads_top_level_feature():
    data = {"agy": {"installation_method": "preinstalled"}}

    assert installation_method(data, "agy") == "preinstalled"


def test_installation_method_reads_dotted_feature_path():
    data = {"packages": {"strace": {"installation_method": "apt"}}}

    assert installation_method(data, "packages.strace") == "apt"


def test_required_installation_method_reads_dotted_feature_path():
    data = {"packages": {"strace": {"installation_method": "apt"}}}

    assert required_installation_method(data, "packages.strace") == "apt"


def test_installation_method_defaults_missing_dotted_path_to_none():
    data = {"packages": {}}

    assert installation_method(data, "packages.strace") == "none"


def test_required_installation_method_rejects_missing_dotted_path():
    data = {"packages": {}}

    with pytest.raises(KeyError, match=r"packages\.strace"):
        required_installation_method(data, "packages.strace")


def test_installation_method_defaults_missing_feature_to_none():
    assert installation_method({}, "agy") == "none"


def test_installation_method_defaults_missing_method_to_none():
    assert installation_method({"agy": {}}, "agy") == "none"


def test_required_installation_method_rejects_missing_method():
    with pytest.raises(KeyError, match=r"agy\.installation_method"):
        required_installation_method({"agy": {}}, "agy")


def test_required_installation_method_rejects_non_string_method():
    with pytest.raises(TypeError, match=r"agy\.installation_method"):
        required_installation_method({"agy": {"installation_method": []}}, "agy")


@pytest.mark.integration
def test_chezmoi_data_contains_agy_installation_method(chezmoi_data):
    assert "agy" in chezmoi_data
    assert installation_method(chezmoi_data, "agy") in AGY_INSTALLATION_METHODS


@pytest.mark.integration
@pytest.mark.parametrize("feature,methods", MARKER_GATED_INSTALLATION_METHODS.items())
def test_marker_gated_installation_method_contract(chezmoi_data, feature, methods):
    assert required_installation_method(chezmoi_data, feature) in methods
