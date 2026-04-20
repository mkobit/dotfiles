import subprocess
import pytest
import os

def run_chezmoi_template(template_content: str) -> str:
    source_dir = os.path.abspath("src/chezmoi")
    result = subprocess.run(
        ["chezmoi", "execute-template", "--source", source_dir, "-i", template_content],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout.strip()

@pytest.mark.integration
def test_claude_statusline_template_generation():
    """Verify additive configurations are injected correctly into the shell wrapper."""
    template_content = """
{{- $data := dict "local_bin_tools" (dict "claude_statusline" (dict "installation" "uv")) "claude_code" (dict "settings" (dict "statusLine" (dict "generators" (list "test1" "test2")))) -}}
{{- includeTemplate ".chezmoitemplates/../dot_local/bin/executable_claude_statusline.tmpl" $data -}}
"""
    output = run_chezmoi_template(template_content)
    assert "exec mise exec -- claude-statusline --generator \"test1\" --generator \"test2\" \"$@\"" in output

@pytest.mark.integration
def test_claude_statusline_template_disabled():
    """Verify subtractive configuration correctly outputs nothing when disabled."""
    template_content = """
{{- $data := dict "local_bin_tools" (dict "claude_statusline" (dict "installation" "disabled")) "claude_code" (dict "settings" (dict "statusLine" (dict "generators" (list "test1" "test2")))) -}}
{{- includeTemplate ".chezmoitemplates/../dot_local/bin/executable_claude_statusline.tmpl" $data -}}
"""
    output = run_chezmoi_template(template_content)
    assert output == ""

@pytest.mark.integration
def test_install_script_generation_enabled():
    """Verify install script correctly generates uv tool install when enabled."""
    template_content = """
{{- $data := dict "local_bin_tools" (dict "jules" (dict "installation" "uv")) "chezmoi" (dict "sourceDir" "/fake/source") -}}
{{- includeTemplate ".chezmoitemplates/../.chezmoiscripts/run_once_after_install_jules.sh.tmpl" $data -}}
"""
    output = run_chezmoi_template(template_content)
    assert "uv tool install --force \"/fake/source/../python/jules_cli\"" in output

@pytest.mark.integration
def test_install_script_generation_disabled():
    """Verify install script correctly generates uv tool uninstall when disabled."""
    template_content = """
{{- $data := dict "local_bin_tools" (dict "jules" (dict "installation" "disabled")) "chezmoi" (dict "sourceDir" "/fake/source") -}}
{{- includeTemplate ".chezmoitemplates/../.chezmoiscripts/run_once_after_install_jules.sh.tmpl" $data -}}
"""
    output = run_chezmoi_template(template_content)
    assert "uv tool uninstall jules || true" in output
