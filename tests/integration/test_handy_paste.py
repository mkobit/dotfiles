import ctypes
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


def helper():
    template = Path.cwd() / "src/chezmoi/dot_local/bin/executable_handy-paste.tmpl"
    assert template.is_file(), "Handy paste helper is missing"
    with tempfile.TemporaryDirectory() as source:
        rendered = subprocess.run(
            [
                "chezmoi",
                "--config",
                "/dev/null",
                "--config-format",
                "toml",
                "--source",
                source,
                "execute-template",
                "--override-data",
                json.dumps(
                    {
                        "text_replacement_pairs": {
                            "EGM": "elephant-goldfish model",
                            "chesmoir": "chezmoi",
                            "Zealage": "Zellij",
                        }
                    }
                ),
                "-f",
                str(template),
            ],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
    namespace = {"__name__": "handy_paste_test"}
    exec(compile(rendered, str(template), "exec"), namespace)
    return namespace


def test_replaces_spoken_words_without_changing_other_text():
    replace = helper()["replace_words"]
    assert replace("EGM, chesmoir. Zealage!\nHi 🐘") == "elephant-goldfish model, chezmoi. Zellij!\nHi 🐘"


def test_replaces_only_complete_words_without_case_sensitivity():
    replace = helper()["replace_words"]
    assert replace("egm EGMing _EGM chesmoirs zealage") == "elephant-goldfish model EGMing _EGM chesmoirs Zellij"


def test_text_events_preserve_multiline_unicode_and_split_within_macos_limit():
    chunks = helper()["text_events"]("A🐘" + "x" * 20 + "\tZ\r\nline")
    assert "".join(value for _, value in chunks) == "A🐘" + "x" * 20 + "\tZ\r\nline"
    assert all(kind == "text" and value[0] not in "\n\r\t" for kind, value in chunks)
    assert all(len(value.encode("utf-16-le")) <= 40 for kind, value in chunks if kind == "text")


def test_leading_newlines_fail_without_synthesizing_return_keys():
    with pytest.raises(RuntimeError, match="Handy history"):
        helper()["text_events"]("\nmessage")


def test_long_control_runs_fail_without_synthesizing_keys():
    with pytest.raises(RuntimeError, match="Handy history"):
        helper()["text_events"]("message" + "\n" * 30)


@pytest.mark.skipif(sys.platform != "darwin", reason="Quartz is only available on macOS")
def test_quartz_event_contains_complete_unicode_without_posting():
    functions = helper()
    quartz, core = functions["keyboard_services"]()
    payload = "abc🐘🦁終"
    event = functions["create_text_event"](quartz, payload)
    try:
        quartz.CGEventKeyboardGetUnicodeString.argtypes = (
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_uint16),
        )
        length = ctypes.c_ulong()
        buffer = (ctypes.c_uint16 * 20)()
        quartz.CGEventKeyboardGetUnicodeString(event, 20, ctypes.byref(length), buffer)
        assert bytes(buffer)[: length.value * 2].decode("utf-16-le") == payload
    finally:
        core.CFRelease(event)


@pytest.mark.skipif(sys.platform != "darwin", reason="Accessibility is only available on macOS")
def test_without_accessibility_access_no_input_is_sent():
    functions = helper()
    quartz, _ = functions["keyboard_services"]()
    if quartz.AXIsProcessTrusted():
        pytest.skip("The test process already has Accessibility access")
    with pytest.raises(RuntimeError, match="Accessibility access"):
        functions["type_text"]("This text must not be inserted")
