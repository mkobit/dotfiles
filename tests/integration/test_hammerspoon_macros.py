import json
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path("src/chezmoi/dot_dotfiles/hammerspoon")


def render_config(tmp_path):
    data = {"hammerspoon": {"window_manager": {"enabled": False}}}
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(tmp_path),
            "--destination",
            str(tmp_path),
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "execute-template",
            "-f",
            "--override-data",
            json.dumps(data),
            str(SOURCE / "config.lua.tmpl"),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def run_lua(script):
    hs = shutil.which("hs")
    if not hs:
        pytest.skip("Hammerspoon CLI is not available")
    result = subprocess.run([hs, "-q", "-t", "5", "-c", script], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_overlay_files_load_in_order_and_fail_independently(tmp_path):
    config_dir = tmp_path / ".dotfiles/hammerspoon"
    snippets = config_dir / "snippets"
    snippets.mkdir(parents=True)
    (snippets / "init.lua").write_text("")
    shutil.copy(SOURCE / "snippets/macros.lua", snippets)
    (config_dir / "config.lua").write_text(render_config(tmp_path))
    path = json.dumps(str(config_dir / "config.lua"))
    script = f"""local env = setmetatable({{}}, {{__index = _G}})
        env._G = env
        env.hs = setmetatable({{alert = {{show = function(msg) env.alerts[#env.alerts + 1] = msg end}},
            printf = function() end}}, {{__index = hs}})
        env.alerts, env.order = {{}}, {{}}
        env.dofile = function(file) return assert(loadfile(file, "t", env))() end
        env.dofile({path})
        return hs.json.encode({{order=env.order, alerts=env.alerts,
            hasTagAction=type(env.DotfilesActions.wrapPromptTag) == "function"}})"""
    assert run_lua(script) == {"order": [], "alerts": [], "hasTagAction": True}

    overlay = config_dir / "overlay"
    overlay.mkdir()
    (overlay / "b.lua").write_text('order[#order + 1] = "b"')
    (overlay / "a.lua").write_text('order[#order + 1] = "a"')
    (overlay / "bad.lua").write_text('error("bad overlay")')
    (overlay / "c.lua").write_text('order[#order + 1] = "c"')
    (overlay / "ignored.txt").write_text('error("not Lua")')
    result = run_lua(script)
    assert result["order"] == ["a", "b", "c"]
    assert result["hasTagAction"] is True
    assert len(result["alerts"]) == 1
    assert "bad.lua" in result["alerts"][0]


def test_tag_ranges_expand_partial_words_and_count_utf16_units():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local cases = {{{{ "copied prompt", 3, 7 }}, {{ "copied prompt", 5, 0 }},
            {{ "🦊 copied prompt!", 6, 7 }}, {{ "x: copied prompt!", 8, 0 }},
            {{ "before copied-prompt after", 12, 0 }}}}
        local out = {{}}
        for _, c in ipairs(cases) do out[#out + 1] = m.plan(c[1], c[2], c[3]) end
        return hs.json.encode(out)"""
    plans = run_lua(script)
    assert [(p["location"], p["length"], p["replacement"], p["cursor"]) for p in plans] == [
        (0, 13, "<copied-prompt></copied-prompt>", 15),
        (0, 6, "<copied></copied>", 8),
        (3, 13, "<copied-prompt></copied-prompt>", 18),
        (3, 6, "<copied></copied>", 11),
        (7, 13, "<copied-prompt></copied-prompt>", 22),
    ]


def test_tag_rejects_unsafe_ranges_and_invalid_names():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        return hs.json.encode({{
            m.plan("🦊 copied", 1, 0) == nil,
            m.plan("3 birds", 1, 0) == nil,
            m.plan("", 0, 0) == nil,
            m.plan("copied!prompt", 2, 8) == nil,
            m.plan("copied", 10, 0) == nil,
            m.plan("café", 2, 0) == nil,
        }})"""
    assert run_lua(script) == [True] * 6


def test_tag_action_checks_accessibility_and_replaces_only_selected_text():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local function run(bundle, writable, focused)
            local state = {{value = "copied prompt", range = {{location = 3, length = 7}}, writes = 0}}
            local element = {{}}
            function element:attributeValue(name)
                if name == "AXRole" then return "AXTextArea" end
                if name == "AXValue" then return state.value end
                if name == "AXSelectedTextRange" then return state.range end
            end
            function element:isAttributeSettable(name) return writable end
            function element:setAttributeValue(name, value)
                state.writes = state.writes + 1
                if name == "AXSelectedTextRange" then state.range = value end
                if name == "AXSelectedText" then
                    state.value = state.value:sub(1, state.range.location) .. value
                        .. state.value:sub(state.range.location + state.range.length + 1)
                end
                return self
            end
            local system = {{attributeValue = function() if focused then return element end end}}
            local api = {{axuielement = {{systemWideElement = function() return system end}},
                application = {{frontmostApplication = function() return {{bundleID = function() return bundle end}} end}}}}
            local result = m.promptTag(api)
            return {{result = result, value = state.value, range = state.range, writes = state.writes}}
        end
        return hs.json.encode({{run("browser", true, true), run("browser", false, true),
            run("com.mitchellh.ghostty", true, true), run("browser", true, false)}})"""
    success, readonly, terminal, nofocus = run_lua(script)
    assert success == {
        "result": True,
        "value": "<copied-prompt></copied-prompt>",
        "range": {"location": 15, "length": 0},
        "writes": 3,
    }
    for result in [readonly, terminal, nofocus]:
        assert result["result"] is False
        assert result["value"] == "copied prompt"
        assert result["writes"] == 0


def test_tag_action_reports_unavailable_field():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local alerts = {{}}
        local api = {{
            alert = {{show = function(text) alerts[#alerts + 1] = text end}},
            axuielement = {{systemWideElement = function() return {{attributeValue = function() return nil end}} end}},
            application = {{frontmostApplication = function() return nil end}},
        }}
        m.wrapPromptTag(api)
        return hs.json.encode(alerts)"""
    assert run_lua(script) == ["Cannot wrap text in this field"]


def test_tag_action_does_not_replace_text_when_selection_write_is_ignored():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local state = {{value="copied prompt", range={{location=3, length=7}}, replacements=0}}
        local element = {{}}
        function element:attributeValue(name)
            if name == "AXRole" then return "AXTextArea" end
            if name == "AXValue" then return state.value end
            if name == "AXSelectedTextRange" then return state.range end
        end
        function element:isAttributeSettable(name) return true end
        function element:setAttributeValue(name, value)
            if name == "AXSelectedText" then state.replacements = state.replacements + 1 end
            return self
        end
        local system = {{attributeValue = function() return element end}}
        local api = {{axuielement = {{systemWideElement = function() return system end}},
            application = {{frontmostApplication = function() return {{bundleID = function() return "browser" end}} end}}}}
        return hs.json.encode({{result=m.promptTag(api), value=state.value,
            range=state.range, replacements=state.replacements}})"""
    assert run_lua(script) == {
        "result": False,
        "value": "copied prompt",
        "range": {"location": 3, "length": 7},
        "replacements": 0,
    }


def test_tag_action_waits_for_selection_and_verifies_typed_text():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local function run(mode)
            local state = {{value="before copied prompt after", range={{location=10, length=7}},
                focused=true, writes=0, cursorWrites=0, typed=0, alerts={{}}, ticks=0, queue={{}}}}
            local element = {{}}
            local app = {{bundleID = function() return "browser" end}}
            function element:attributeValue(name)
                if name == "AXRole" then return "AXTextArea" end
                if name == "AXValue" then return state.value end
                if name == "AXSelectedTextRange" then return state.range end
            end
            function element:isAttributeSettable(name) return name == "AXSelectedTextRange" or name == "AXValue" end
            function element:setAttributeValue(name, value)
                if name == "AXValue" then state.writes = state.writes + 1 end
                if name == "AXSelectedTextRange" and value.length == 0 then state.cursorWrites = state.cursorWrites + 1 end
                if name == "AXSelectedTextRange" then state.pendingRange = value; state.rangeAt = state.ticks + 3 end
                return self
            end
            local system = {{attributeValue = function() if state.focused then return element end end}}
            local api = {{axuielement = {{systemWideElement = function() return system end}},
                application = {{frontmostApplication = function() return app end}},
                timer = {{doAfter = function(_, fn) state.queue[#state.queue + 1] = fn; return true end}},
                alert = {{show = function(message) state.alerts[#state.alerts + 1] = message end}},
                eventtap = {{keyStrokes = function(text, target)
                    assert(target == app)
                    state.typed = state.typed + 1
                    state.value = "before <c after"
                    state.expected = "before " .. text .. " after"
                    state.endRange = {{location=7 + #text, length=0}}
                    state.valueAt = state.ticks + 3
                end}}}}
            local result = m.promptTag(api)
            local overlap = m.promptTag(api)
            while #state.queue > 0 and state.ticks < 100 do
                state.ticks = state.ticks + 1
                if mode == "focus" and state.ticks == 2 then state.focused = false end
                if mode == "value" and state.ticks == 2 then state.value = "changed elsewhere" end
                if state.pendingRange and state.ticks >= state.rangeAt and mode ~= "timeout" then
                    state.range = state.pendingRange; state.pendingRange = nil
                end
                if state.expected and state.ticks >= state.valueAt and mode ~= "type_timeout" then
                    state.value = mode == "unexpected" and "changed elsewhere" or state.expected
                    state.expected = nil
                    if mode == "selection" then state.range = {{location=2, length=0}}
                    elseif mode == "delay_end" then state.endRangeAt = state.ticks + 3
                    else state.range = state.endRange end
                end
                if state.endRangeAt and state.ticks >= state.endRangeAt then
                    state.range = state.endRange; state.endRangeAt = nil
                end
                table.remove(state.queue, 1)()
            end
            return {{result=result, value=state.value, range=state.range, writes=state.writes,
                typed=state.typed, alerts=state.alerts, ticks=state.ticks, pending=#state.queue,
                overlap=overlap, cursorWrites=state.cursorWrites}}
        end
        return hs.json.encode({{run("success"), run("timeout"), run("focus"), run("value"),
            run("unexpected"), run("type_timeout"), run("selection"), run("delay_end")}})"""
    success, timeout, focus, value, unexpected, type_timeout, selection, delay_end = run_lua(script)
    assert success["result"] is True
    assert success["typed"] == 1
    assert success["value"] == "before <copied-prompt></copied-prompt> after"
    assert success["range"] == {"location": 22, "length": 0}
    assert success["alerts"] == []
    for failure in (timeout, focus, value):
        assert failure["result"] is True
        assert failure["typed"] == 0
        assert failure["alerts"] == ["Cannot wrap text in this field"]
    assert unexpected["typed"] == 1
    assert unexpected["value"] == "changed elsewhere"
    assert unexpected["alerts"] == ["Could not verify tag insertion; text may have changed"]
    assert type_timeout["typed"] == 1
    assert type_timeout["alerts"] == ["Could not verify tag insertion; text may have changed"]
    assert selection["range"] == {"location": 2, "length": 0}
    assert selection["cursorWrites"] == 0
    assert selection["alerts"] == ["Could not verify tag insertion; text may have changed"]
    assert delay_end["range"] == {"location": 22, "length": 0}
    assert delay_end["alerts"] == []
    for result in (success, timeout, focus, value, unexpected, type_timeout, selection, delay_end):
        assert result["writes"] == 0
        assert result["overlap"] is False
        assert result["ticks"] < 100
        assert result["pending"] == 0


def test_direct_replacement_warns_if_cursor_cannot_be_set():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local state = {{value="copied prompt", range={{location=3, length=7}}, alerts={{}}}}
        local element = {{}}
        function element:attributeValue(name)
            if name == "AXRole" then return "AXTextArea" end
            if name == "AXValue" then return state.value end
            if name == "AXSelectedTextRange" then return state.range end
        end
        function element:isAttributeSettable(name) return true end
        function element:setAttributeValue(name, value)
            if name == "AXSelectedTextRange" and value.length > 0 then state.range = value end
            if name == "AXSelectedText" then state.value = value end
            return self
        end
        local system = {{attributeValue = function() return element end}}
        local api = {{axuielement = {{systemWideElement = function() return system end}},
            application = {{frontmostApplication = function() return {{bundleID = function() return "editor" end}} end}},
            alert = {{show = function(message) state.alerts[#state.alerts + 1] = message end}}}}
        m.wrapPromptTag(api)
        return hs.json.encode({{value=state.value, alerts=state.alerts}})"""
    assert run_lua(script) == {
        "value": "<copied-prompt></copied-prompt>",
        "alerts": ["Could not verify tag insertion; text may have changed"],
    }
