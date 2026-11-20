import asyncio
import json
import os
import shutil
import sys
import tempfile
import uuid
from contextlib import suppress
from pathlib import Path

import pytest
from integration_support.chezmoi import chezmoi_argv, run_chezmoi

SOURCE = Path("src/chezmoi/dot_dotfiles/hammerspoon")
pytestmark = pytest.mark.asyncio


async def render_config(tmp_path):
    data = {"hammerspoon": {"window_manager": {"enabled": False}}}
    result = await run_chezmoi(
        chezmoi_argv(
            "--config-format",
            "toml",
            "execute-template",
            "-f",
            "--override-data",
            json.dumps(data),
            str(SOURCE / "config.lua.tmpl"),
            source=tmp_path,
            destination=tmp_path,
            config="/dev/null",
        ),
    )
    if result.returncode:
        raise RuntimeError(f"chezmoi failed with exit code {result.returncode}:\n{result.stderr}")
    return result.stdout


async def run_lua(script, *, timeout=10):
    hs = shutil.which(os.environ.get("HAMMERSPOON_CLI", "hs"))
    if not hs:
        if os.environ.get("HAMMERSPOON_TEST_REQUIRED") == "1":
            pytest.fail("Hammerspoon CLI is required for this CI job")
        pytest.skip("Hammerspoon CLI is not available")
    args = [hs, "-q", "-t", "5", "-c", script]
    process = await asyncio.create_subprocess_exec(
        # hs reads stdin after -c; an inherited CI pipe can remain open.
        *args,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
            await process.communicate()
    if process.returncode:
        raise RuntimeError(
            f"Hammerspoon CLI failed with exit code {process.returncode}:\n"
            f"stderr: {stderr.decode(errors='replace')}\nstdout: {stdout.decode(errors='replace')}"
        )
    return json.loads(stdout)


@pytest.fixture
def hammerspoon_scratch():
    scratch = (Path.cwd() / ".scratch").resolve()
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hammerspoon-", dir=scratch) as directory:
        yield Path(directory)


def assert_warning(alerts):
    assert len(alerts) == 1
    assert isinstance(alerts[0], str) and alerts[0].strip()


def assert_text_may_have_changed(alerts):
    assert_warning(alerts)
    warning = alerts[0].lower()
    assert "text" in warning
    assert any(word in warning for word in ("changed", "modified"))
    assert any(word in warning for word in ("may", "might", "could", "whether", "possibly"))


async def test_overlay_files_load_in_order_and_fail_independently(hammerspoon_scratch):
    config_dir = hammerspoon_scratch / ".dotfiles/hammerspoon"
    snippets = config_dir / "snippets"
    snippets.mkdir(parents=True)
    (snippets / "init.lua").write_text("")
    shutil.copy(SOURCE / "snippets/macros.lua", snippets)
    (config_dir / "config.lua").write_text(await render_config(hammerspoon_scratch))
    path = json.dumps(str(config_dir / "config.lua"))
    script = f"""local env = setmetatable({{}}, {{__index = _G}})
        env._G = env
        env.hs = setmetatable({{alert = {{show = function(msg) env.alerts[#env.alerts + 1] = msg end}},
            printf = function() end, menubar = {{new = function() return nil end}}}}, {{__index = hs}})
        env.alerts, env.order = {{}}, {{}}
        env.dofile = function(file) return assert(loadfile(file, "t", env))() end
        env.dofile({path})
        return hs.json.encode({{order=env.order, alerts=env.alerts,
            hasTagAction=type(env.DotfilesActions.wrapPromptTag) == "function"}})"""
    assert await run_lua(script) == {"order": [], "alerts": [], "hasTagAction": True}

    overlay = config_dir / "overlay"
    overlay.mkdir()
    (overlay / "b.lua").write_text('order[#order + 1] = "b"')
    (overlay / "a.lua").write_text('order[#order + 1] = "a"')
    (overlay / "bad.lua").write_text('error("bad overlay")')
    (overlay / "c.lua").write_text('order[#order + 1] = "c"')
    (overlay / "ignored.txt").write_text('error("not Lua")')
    (overlay / "directory.lua").mkdir()
    result = await run_lua(script)
    assert result["order"] == ["a", "b", "c"]
    assert result["hasTagAction"] is True
    assert len(result["alerts"]) == 1
    assert "bad.lua" in result["alerts"][0]


async def test_nested_change_reloads_after_watcher_garbage_collection(tmp_path):
    if not shutil.which(os.environ.get("HAMMERSPOON_CLI", "hs")):
        if os.environ.get("HAMMERSPOON_TEST_REQUIRED") == "1":
            pytest.fail("Hammerspoon CLI is required for this CI job")
        pytest.skip("Hammerspoon CLI is not available")
    nested = tmp_path / "overlay"
    nested.mkdir()
    config_dir = json.dumps(str(tmp_path))
    init_path = json.dumps(str((SOURCE / "init.lua").resolve()))
    watcher_key = json.dumps("_codexWatcherTestEnv_" + uuid.uuid4().hex)
    try:
        await run_lua(f"""local env = setmetatable({{}}, {{__index = _G}})
            env._G = env
            env.count = 0
            env.hs = setmetatable({{configdir = {config_dir},
                reload = function() env.count = env.count + 1 end,
                alert = {{show = function() end}}}}, {{__index = hs}})
            env.require = function() return {{}} end
            env.dofile = function() end
            assert(loadfile({init_path}, "t", env))()
            _G[{watcher_key}] = env
            collectgarbage("collect")
            return hs.json.encode({{true}})""")
        (nested / "changed.lua").write_text("-- changed")
        try:
            async with asyncio.timeout(5):
                while not (await run_lua(f"return hs.json.encode({{_G[{watcher_key}].count}})"))[0]:
                    await asyncio.sleep(0.2)
        except TimeoutError:
            pytest.fail("Hammerspoon did not reload after a nested Lua file changed")
    finally:
        original_error = sys.exception()
        try:
            await run_lua(f"""local env = _G[{watcher_key}]
                if env and env.DotfilesConfigWatcher then
                    env.DotfilesConfigWatcher:stop()
                end
                _G[{watcher_key}] = nil
                collectgarbage("collect")
                return hs.json.encode({{true}})""")
        except Exception as cleanup_error:
            if original_error is None:
                raise
            original_error.add_note(f"Hammerspoon watcher cleanup failed: {cleanup_error!r}")


async def test_tag_ranges_expand_partial_words_and_count_utf16_units():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    script = f"""local m = dofile({path})
        local cases = {{{{ "copied prompt", 3, 7 }}, {{ "copied prompt", 5, 0 }},
            {{ "🦊 copied prompt!", 6, 7 }}, {{ "x: copied prompt!", 8, 0 }},
            {{ "before copied-prompt after", 12, 0 }}}}
        local out = {{}}
        for _, c in ipairs(cases) do out[#out + 1] = m.plan(c[1], c[2], c[3]) end
        return hs.json.encode(out)"""
    plans = await run_lua(script)
    assert [(p["location"], p["length"], p["replacement"], p["cursor"]) for p in plans] == [
        (0, 13, "<copied-prompt></copied-prompt>", 15),
        (0, 6, "<copied></copied>", 8),
        (3, 13, "<copied-prompt></copied-prompt>", 18),
        (3, 6, "<copied></copied>", 11),
        (7, 13, "<copied-prompt></copied-prompt>", 22),
    ]


async def test_tag_rejects_unsafe_ranges_and_invalid_names():
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
    assert await run_lua(script) == [True] * 6


async def test_tag_action_checks_accessibility_and_replaces_only_selected_text():
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
    success, readonly, terminal, nofocus = await run_lua(script)
    assert success["result"] is True
    assert success["value"] == "<copied-prompt></copied-prompt>"
    assert success["range"] == {"location": 15, "length": 0}
    for result in [readonly, terminal, nofocus]:
        assert result["result"] is False
        assert result["value"] == "copied prompt"
        assert result["writes"] == 0


async def test_tag_action_reports_unavailable_field():
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
    assert_warning(await run_lua(script))


async def test_tag_action_does_not_replace_text_when_selection_write_is_ignored():
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
    assert await run_lua(script) == {
        "result": False,
        "value": "copied prompt",
        "range": {"location": 3, "length": 7},
        "replacements": 0,
    }


async def test_tag_action_waits_for_selection_and_verifies_typed_text():
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
                typed=state.typed, alerts=state.alerts, pending=#state.queue,
                overlap=overlap, cursorWrites=state.cursorWrites}}
        end
        return hs.json.encode({{run("success"), run("timeout"), run("focus"), run("value"),
            run("unexpected"), run("type_timeout"), run("selection"), run("delay_end")}})"""
    success, timeout, focus, value, unexpected, type_timeout, selection, delay_end = await run_lua(script)
    assert success["result"] is True
    assert success["typed"] == 1
    assert success["value"] == "before <copied-prompt></copied-prompt> after"
    assert success["range"] == {"location": 22, "length": 0}
    assert success["alerts"] == []
    for failure in (timeout, focus, value):
        assert failure["result"] is True
        assert failure["typed"] == 0
        assert_warning(failure["alerts"])
    assert unexpected["typed"] == 1
    assert unexpected["value"] == "changed elsewhere"
    assert_text_may_have_changed(unexpected["alerts"])
    assert type_timeout["typed"] == 1
    assert_text_may_have_changed(type_timeout["alerts"])
    assert selection["range"] == {"location": 2, "length": 0}
    assert selection["cursorWrites"] == 0
    assert_text_may_have_changed(selection["alerts"])
    assert delay_end["range"] == {"location": 22, "length": 0}
    assert delay_end["alerts"] == []
    for result in (success, timeout, focus, value, unexpected, type_timeout, selection, delay_end):
        assert result["writes"] == 0
        assert result["overlap"] is False
        assert result["pending"] == 0


async def test_direct_replacement_warns_if_cursor_cannot_be_set():
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
    result = await run_lua(script)
    assert result["value"] == "<copied-prompt></copied-prompt>"
    assert_text_may_have_changed(result["alerts"])


async def test_tag_plan_preserves_surrounding_text_at_selection_boundaries():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    plans = await run_lua(f"""local m = dofile({path})
        return hs.json.encode({{
            m.plan("before copied prompt after", 10, 7),
            m.plan("🦊 copied prompt!", 6, 7),
            m.plan("one\\t\\ttwo", 0, 8),
            m.plan("copied", 6, 0),
            m.plan("_copied-2", 0, 0),
        }})""")
    assert [(p["value"], p["cursor"]) for p in plans] == [
        ("before <copied-prompt></copied-prompt> after", 22),
        ("🦊 <copied-prompt></copied-prompt>!", 18),
        ("<one-two></one-two>", 9),
        ("<copied></copied>", 8),
        ("<_copied-2></_copied-2>", 11),
    ]


async def test_tag_plan_rejects_malformed_and_multiline_ranges():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    result = await run_lua(f"""local m = dofile({path})
        return hs.json.encode({{
            m.plan("copied", -1, 0) == nil,
            m.plan("copied", 1.5, 0) == nil,
            m.plan("copied", 0, -1) == nil,
            m.plan("copied", 0, 99) == nil,
            m.plan("copied\\nprompt", 0, 13) == nil,
            m.plan(string.char(255), 0, 0) == nil,
            m.plan("🦊 copied", 0, 1) == nil,
        }})""")
    assert result == [True] * 7


async def test_text_insertion_targets_the_app_and_rejects_secure_or_missing_fields():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    result = await run_lua(f"""local m = dofile({path})
        local function run(bundle, role, subrole, focused)
            local typed = {{}}
            local app = {{bundleID=function() return bundle end}}
            local element = {{attributeValue=function(_, name)
                if name == "AXRole" then return role end
                if name == "AXSubrole" then return subrole end
            end}}
            local system = {{attributeValue=function() if focused then return element end end}}
            local api = {{application={{frontmostApplication=function() return app end}},
                axuielement={{systemWideElement=function() return system end}},
                eventtap={{keyStrokes=function(text, target)
                    assert(target == app)
                    typed[#typed + 1] = text
                end}}}}
            return {{ok=m.insertText("literal <tag>🦊\\n", api), typed=typed}}
        end
        return hs.json.encode({{run("com.google.Chrome", "AXTextArea", nil, true),
            run("com.todesktop.230313mzl4w4u92", "AXTextArea", nil, true),
            run("com.mitchellh.ghostty", "AXTextArea", nil, true),
            run("browser", "AXTextField", "AXSecureTextField", true),
            run("browser", "AXButton", nil, true), run("browser", "AXTextArea", nil, false)}})""")
    for item in result[:3]:
        assert item == {"ok": True, "typed": ["literal <tag>🦊\n"]}
    for item in result[3:]:
        assert item == {"ok": False, "typed": []}


async def test_macro_menu_restores_the_saved_target_and_stops_if_focus_changes():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    result = await run_lua(f"""local m = dofile({path})
        local function run(mode)
            local queue, actions, alerts = {{}}, {{}}, {{}}
            local saved = {{}}
            local other = {{}}
            local activations = 0
            local app = {{activate=function() activations=activations + 1 end}}
            local current = app
            local focus = saved
            local factory, menuTitle
            local menu = {{setTitle=function(self, text) menuTitle=text; return self end,
                setMenu=function(self, fn) factory=fn; return self end, delete=function() end}}
            local api = {{menubar={{new=function() return menu end}},
                application={{frontmostApplication=function() return current end}},
                axuielement={{systemWideElement=function()
                    return {{attributeValue=function() return focus end}}
                end}},
                timer={{doAfter=function(_, fn) queue[#queue + 1] = fn; return {{}} end}},
                alert={{show=function(text) alerts[#alerts + 1] = text end}}}}
            m.actions = {{}}
            m.register("Insert test text", function(received)
                assert(received == api)
                actions[#actions + 1] = "inserted"
            end)
            m.startMenu(api)
            local items = factory()
            current = {{}}
            focus = other
            items[1].fn()
            if mode == "both" or mode == "app" then current=app end
            if mode == "both" or mode == "focus" then focus=saved end
            local ticks=0
            while #queue > 0 and ticks < 100 do
                ticks=ticks + 1
                table.remove(queue, 1)()
            end
            return {{title=menuTitle, item=items[1].title, actions=actions, alerts=alerts, pending=#queue,
                activations=activations}}
        end
        return hs.json.encode({{run("both"), run("app"), run("focus"), run("neither")}})""")
    success, *failures = result
    assert success == {
        "title": "Macros",
        "item": "Insert test text",
        "actions": ["inserted"],
        "alerts": [],
        "pending": 0,
        "activations": 1,
    }
    for failure in failures:
        assert failure["actions"] == []
        assert failure["pending"] == 0
        assert failure["activations"] == 1
        assert_warning(failure["alerts"])


async def test_direct_replacement_preserves_unicode_prefix_and_places_cursor_between_tags():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    result = await run_lua(f"""local m = dofile({path})
        local state={{value="🦊 copied prompt!", range={{location=6, length=7}}, wholeWrites=0}}
        local element={{}}
        function element:attributeValue(name)
            if name == "AXRole" then return "AXTextArea" end
            if name == "AXValue" then return state.value end
            if name == "AXSelectedTextRange" then return state.range end
        end
        function element:isAttributeSettable() return true end
        function element:setAttributeValue(name, value)
            if name == "AXSelectedTextRange" then state.range=value end
            if name == "AXValue" then state.wholeWrites=state.wholeWrites + 1 end
            if name == "AXSelectedText" then
                assert(state.range.location == 3 and state.range.length == 13)
                assert(value == "<copied-prompt></copied-prompt>")
                state.value="🦊 " .. value .. "!"
            end
            return self
        end
        local app={{bundleID=function() return "browser" end}}
        local api={{application={{frontmostApplication=function() return app end}},
            axuielement={{systemWideElement=function()
                return {{attributeValue=function() return element end}}
            end}}}}
        state.ok=m.promptTag(api)
        return hs.json.encode(state)""")
    assert result == {
        "value": "🦊 <copied-prompt></copied-prompt>!",
        "range": {"location": 18, "length": 0},
        "wholeWrites": 0,
        "ok": True,
    }


async def test_text_insertion_stops_when_secure_input_is_enabled():
    path = json.dumps(str((SOURCE / "snippets/macros.lua").resolve()))
    result = await run_lua(f"""local m = dofile({path})
        local typed=0
        local app={{}}
        local element={{attributeValue=function(_, name)
            if name == "AXRole" then return "AXTextArea" end
        end}}
        local api={{application={{frontmostApplication=function() return app end}},
            axuielement={{systemWideElement=function()
                return {{attributeValue=function() return element end}}
            end}}, eventtap={{isSecureInputEnabled=function() return true end,
                keyStrokes=function() typed=typed + 1 end}}}}
        return hs.json.encode({{ok=m.insertText("private", api), typed=typed}})""")
    assert result == {"ok": False, "typed": 0}


async def test_lua_runner_closes_inherited_input(monkeypatch):
    original = asyncio.create_subprocess_exec
    read_fd, write_fd = os.pipe()

    async def with_open_parent_input(*args, **kwargs):
        # Simulate a CI parent whose input pipe remains open for the full job.
        kwargs.setdefault("stdin", read_fd)
        return await original(*args, **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", with_open_parent_input)
    try:
        assert await run_lua("return hs.json.encode({true})", timeout=2) == [True]
    finally:
        os.close(read_fd)
        os.close(write_fd)


async def test_lua_runner_kills_and_reaps_timed_out_process(monkeypatch):
    original = asyncio.create_subprocess_exec
    processes = []

    async def stalled_cli(*args, **kwargs):
        process = await original(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(shutil, "which", lambda _: sys.executable)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", stalled_cli)
    with pytest.raises(TimeoutError):
        await run_lua("return true", timeout=0.1)
    assert len(processes) == 1
    assert processes[0].returncode is not None


async def test_lua_runner_fails_when_ci_requires_missing_cli(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    monkeypatch.setenv("HAMMERSPOON_TEST_REQUIRED", "1")
    with pytest.raises(pytest.fail.Exception, match="required for this CI job"):
        await run_lua("return true")
