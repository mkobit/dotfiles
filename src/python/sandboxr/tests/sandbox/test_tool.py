from sandboxr.sandbox.tool import adapt_command


def test_claude_gets_dangerously_skip_permissions():
    cmd, _env = adapt_command(["claude", "--print", "hi"], {})
    assert "--dangerously-skip-permissions" in cmd


def test_claude_injects_settings_when_file_exists(tmp_path):
    settings = tmp_path / "autonomous-settings.json"
    settings.write_text("{}")
    cmd, _env = adapt_command(["claude"], {}, claude_settings=settings)
    assert "--settings" in cmd
    assert str(settings) in cmd


def test_claude_does_not_duplicate_settings_flag():
    cmd, _env = adapt_command(["claude", "--settings", "/existing.json"], {})
    assert cmd.count("--settings") == 1


def test_agy_gets_dangerously_skip_permissions():
    cmd, _env = adapt_command(["agy", "run"], {})
    assert "--dangerously-skip-permissions" in cmd


def test_agy_does_not_get_sandbox_flag():
    cmd, _env = adapt_command(["agy", "run"], {})
    assert "--sandbox" not in cmd


def test_opencode_sets_config_env():
    _cmd, env = adapt_command(["opencode"], {})
    assert "OPENCODE_CONFIG" in env


def test_unknown_tool_passes_through():
    cmd, env = adapt_command(["bash", "-c", "echo hi"], {})
    assert cmd == ["bash", "-c", "echo hi"]
    assert env == {}
