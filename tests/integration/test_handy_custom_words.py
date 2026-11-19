import json
import subprocess
from pathlib import Path


def test_handy_custom_words_preserve_existing_settings(tmp_path):
    template = Path("src/chezmoi/Library/Application Support/com.pais.handy/modify_settings_store.json")
    data = {
        "handy": {"custom_words": {"egm": "EGM", "chezmoi": "chezmoi", "zellij": "Zellij"}},
        "text_replacements": {"chi": "Kai"},
    }
    command = [
        "chezmoi",
        "--source",
        str(tmp_path),
        "--config",
        "/dev/null",
        "--config-format",
        "toml",
        "execute-template",
        "-f",
        "--with-stdin",
        "--override-data",
        json.dumps(data),
        str(template),
    ]
    original = {"settings": {"custom_words": ["existing", "chezmoi"], "paste_method": "direct"}}
    result = subprocess.run(command, input=json.dumps(original), capture_output=True, text=True, check=True).stdout
    assert json.loads(result) == {
        "settings": {"custom_words": ["EGM", "Kai", "Zellij", "chezmoi", "existing"], "paste_method": "direct"}
    }
    repeated = subprocess.run(command, input=result, capture_output=True, text=True, check=True).stdout
    assert repeated == result
