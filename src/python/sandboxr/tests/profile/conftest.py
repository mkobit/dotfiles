import pytest

from sandboxr.profile.loader import load_config

BASE_TOML = """
default_profile = "autonomous"

[profiles.autonomous]
enabled = true
backend = "auto"
project_write = true
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.readonly]
enabled = true
backend = "auto"
project_write = false
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.disabled]
enabled = false
backend = "auto"
project_write = true
network = "shared"
"""


@pytest.fixture
def write_config(tmp_path):
    def _write(text):
        path = tmp_path / "sandbox.toml"
        path.write_text(text)
        return path

    return _write


@pytest.fixture
def config(write_config):
    return load_config(write_config(BASE_TOML))


@pytest.fixture
def base_toml() -> str:
    return BASE_TOML
