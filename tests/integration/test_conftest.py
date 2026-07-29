import os

from conftest import _chezmoi_argv


def test_chezmoi_argv_always_includes_source(monkeypatch):
    monkeypatch.delenv("CHEZMOI_CACHE_DIR", raising=False)
    monkeypatch.delenv("CHEZMOI_CONFIG", raising=False)
    monkeypatch.delenv("CHEZMOI_DEST", raising=False)

    argv = _chezmoi_argv("managed")

    assert argv == ["chezmoi", "--source", os.getcwd(), "managed"]


def test_chezmoi_argv_includes_cache_config_destination_when_set(monkeypatch):
    monkeypatch.setenv("CHEZMOI_CACHE_DIR", "/tmp/cache")
    monkeypatch.setenv("CHEZMOI_CONFIG", "/tmp/config.toml")
    monkeypatch.setenv("CHEZMOI_DEST", "/tmp/dest")

    argv = _chezmoi_argv("data", "--format=json")

    assert argv == [
        "chezmoi",
        "--source",
        os.getcwd(),
        "--cache",
        "/tmp/cache",
        "--config",
        "/tmp/config.toml",
        "--destination",
        "/tmp/dest",
        "data",
        "--format=json",
    ]
