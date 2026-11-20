# Hammerspoon macros

Load macros from [the base module](../src/chezmoi/dot_dotfiles/hammerspoon/snippets/macros.lua).
Load local actions from `.dotfiles/hammerspoon/overlay/*.lua` in file name order.
An overlay file error shows an alert and does not stop the other files.

Select **Macros** in the macOS menu bar to run an action without its hotkey.
Put the cursor in the target text field before you open the menu.
The menu keeps the target app and field from the time you open it.
It restores the app and runs the action only when that field has focus.
It stops if the app or field cannot be restored.

Register an overlay action with `DotfilesActions.register(title, function(api) ... end)`.
Use `DotfilesActions.insertText(text, api)` to insert literal text in the focused field.
The function rejects secure fields and active secure input.
It sends text to the target app with [`hs.eventtap.keyStrokes`](https://www.hammerspoon.org/docs/hs.eventtap.html#keyStrokes).
It does not confirm that the app accepted every character.
The menu uses [`hs.menubar`](https://www.hammerspoon.org/docs/hs.menubar.html#setMenu).

## Prompt tags

**Wrap prompt tag** expands a partial selection to complete ASCII words.
With no selection, it uses the word at the cursor.
It changes spaces and tabs to hyphens.
For example, `copied prompt` becomes `<copied-prompt></copied-prompt>`.
It puts the cursor between the tags.
It preserves text before and after the selected words.
It rejects invalid tag names and ranges that split a UTF-16 character.

The action needs a readable text value and a writable text selection from the macOS Accessibility API.
It replaces the selected text when that attribute is writable.
Otherwise, it can type into a verified selection and wait for the text and cursor changes.
It stops on an unexpected focus, text, or selection change.
It warns when insertion might have changed text but cannot be confirmed.
It does not replace the complete field value.

## App checks

Read-only checks ran on macOS on November 20, 2026, with Hammerspoon 1.1.1.
They checked the actual Accessibility attributes of running apps.
They did not insert text in existing user fields.

| App | Observed result | Test still required |
| --- | --- | --- |
| Chrome 157.0.8103.79 | A focused `AXTextArea` exposed a text value and writable selection, selected text, and value attributes. | Tag expansion, cursor placement, literal insertion, and menu focus in a scratch textarea and the intended web apps. |
| Cursor 3.30.14 | The running app did not expose `AXFocusedUIElement` in its current state. | Test an editor and a chat field with accessibility support enabled. Check tag and insertion behavior separately. |
| Ghostty 1.4.0 | A focused `AXTextArea` exposed a text value and selection. Selection, selected text, and value were all read-only. | Literal insertion and menu focus in an isolated terminal. |

A Chrome scratch page was opened for a tag test.
The scratch field did not have focus when the guarded test ran.
The action did not write text.
The laptop then locked, and macOS reported `com.apple.loginwindow` as the front app.
App interaction tests stopped at the lock screen.
No tag or cursor result was verified in a real app during these checks.

Ghostty remains excluded from prompt tag edits.
Its Accessibility value describes terminal text, not the editable shell command buffer.
Its installed scripting dictionary supports `input text` and `send key`, but does not expose a writable command buffer or its cursor.
These commands can insert text, but cannot safely identify and replace a partial shell word.
Hammerspoon can send literal text to Ghostty through targeted keystrokes.
Do not use blind delete or cursor key sequences to add tag support.
Terminal editor key rules differ, and such sequences can change or execute an existing command.

## Manual checks

Use disposable fields and an isolated terminal with no command to execute.
Keep real documents and shell commands out of the test.

1. In a Chrome textarea, select part of `copied prompt` between `before ` and ` after`.
2. Run **Wrap prompt tag** from the menu.
3. Check the complete tag, unchanged surrounding text, and the cursor between the tags.
4. Repeat with no selection and with an emoji before the tag word.
5. Repeat in a Cursor editor and a Cursor chat field.
6. Run each literal insertion action in Chrome, Cursor, and an isolated Ghostty terminal.
7. Check that opening the menu does not send text to another field.
8. Check that tag edits in Ghostty and secure fields show a warning and leave text unchanged.

## Automated config check

[The marked config test](../tests/integration/test_hammerspoon_macros.py) loads the rendered `init.lua` in a dedicated Hammerspoon process.
It checks that the config, macro actions, and menu load without an error.
Its fixture owns startup, process deadlines, logs, and cleanup.
It does not test text insertion, cursor placement, or app behavior.
Those checks remain manual.

CI excludes the `hammerspoon` marker from the general integration run.
The macOS job runs it separately with `--start-hammerspoon`.
The option starts an app, so do not use it during desktop work.
Without that option, the test skips and does not start Hammerspoon.

`hs` uses IPC to a running Hammerspoon app; it cannot run Lua on its own.
See [the IPC module](https://www.hammerspoon.org/docs/hs.ipc.html).
[The prior macOS run](https://github.com/mkobit/dotfiles/actions/runs/44795856355) failed during startup, before pytest ran.
The exact cause remains unconfirmed.
A local probe confirmed that open standard input can hold `hs` open after `-c`.
The fixture closes standard input and limits the full CLI process.
The new config check still needs a GitHub runner result.

## Test cost

[The duration hook](../tests/integration/conftest.py) writes the 20 slowest integration tests to the GitHub job summary.
It includes setup, call, and teardown time.
Shared fixture setup is charged to its first test.
A report write failure does not fail the tests.

[The setup skill fixture](../tests/integration/test_docker_sandboxes_skill.py) applies five skill directories twice and compares their bytes.
It uses separate source, destination, configuration, cache, and persistent state paths.
It excludes scripts and external downloads, but inherits the host environment.
It does not test full-machine apply idempotency.
The fixture now runs once per module because its consumers only read the result.
Four target tests took 11.14 seconds before this change and 6.71 seconds after it.
Fixture setup fell from 6.07 seconds across repeated runs to one 1.85-second run.
