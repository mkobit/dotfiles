from unittest.mock import Mock

import pytest
from conftest import _is_shellcheck_candidate_file
from test_shellcheck import test_shellcheck as run_shellcheck


@pytest.mark.parametrize(
    "source_relative",
    [
        "executable_foo.sh",
        "private_executable_foo.sh",
        "readonly_executable_foo.sh",
        "empty_executable_foo.sh",
        "encrypted_private_readonly_empty_executable_foo.sh.tmpl",
        "create_private_executable_foo.sh",
        "dir/private_executable_foo.sh",
        "modify_dot_bashrc.tmpl",
        "modify_dot_bash_profile.tmpl",
        # Not a chezmoi-valid attribute order (readonly_ before private_), but the
        # regex deliberately doesn't enforce ordering: over-matching only adds a
        # harmless extra shellcheck run, under-matching silently drops coverage.
        "readonly_private_executable_foo.sh",
    ],
)
def test_is_shellcheck_candidate_file_matches_executable_and_modify(source_relative):
    assert _is_shellcheck_candidate_file(source_relative) is True


@pytest.mark.parametrize(
    "source_relative",
    [
        "dot_bashrc.tmpl",
        "private_readonly_foo.sh",
        "foo_executable_bar.sh",
    ],
)
def test_is_shellcheck_candidate_file_rejects_non_executable_non_modify(source_relative):
    assert _is_shellcheck_candidate_file(source_relative) is False


def test_shellcheck_skips_modify_template_before_render(tmp_path):
    source = tmp_path / "modify_settings.json"
    source.write_text('{{- /* chezmoi:modify-template */ -}}\n{{ fail "requires real input" }}\n')
    with pytest.raises(pytest.skip.Exception, match="modify-template"):
        run_shellcheck({"sourceAbsolute": str(source)}, None, None)


def test_shellcheck_renders_executable_modify_script(tmp_path):
    source = tmp_path / "modify_dot_bashrc.tmpl"
    source.write_text("#!/bin/sh\nprintf shell\n")
    host = Mock()
    host.run.side_effect = RuntimeError("render called")
    with pytest.raises(RuntimeError, match="render called"):
        run_shellcheck({"sourceAbsolute": str(source)}, host, lambda *args: "render")
