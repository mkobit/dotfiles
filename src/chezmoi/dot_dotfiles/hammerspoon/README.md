# Hammerspoon

[`init.lua`](init.lua) loads [`config.lua.tmpl`](config.lua.tmpl) from the directory selected by `MJConfigFile`.
Macro code is in [`snippets/macros.lua`](snippets/macros.lua).
Local additions load from `overlay/*.lua` in file name order.

## Macros

Put the cursor in a text field, then select **Macros** in the menu bar.
**Wrap prompt tag** expands the selected ASCII words, or the word at the cursor, into a tag pair.
For example, `copied prompt` becomes `<copied-prompt></copied-prompt>`, with the cursor between the tags.
The action preserves surrounding text and rejects secure fields and unsupported selections.

Register an overlay menu action with `DotfilesActions.register(title, callback)`.
Use `DotfilesActions.insertText(text, api)` for literal insertion; the optional `api` defaults to `hs`.
Insertion uses [`hs.eventtap.keyStrokes`](https://www.hammerspoon.org/docs/hs.eventtap.html#keyStrokes) and cannot confirm that every character was accepted.

Ghostty tag editing is disabled: its Accessibility text and selection are read-only terminal output, not the editable command buffer.
Literal insertion can send text to Ghostty, but still needs a manual check.
Chrome exposed writable text attributes; Cursor needs checks in both editor and chat fields.
No real app insertion or cursor result has been verified.

## Checks

[The CI test](../../../../tests/integration/test_hammerspoon_macros.py) checks that the rendered config, actions, and menu load in Hammerspoon.
It does not test app behavior.
The `hammerspoon` marker selects it; `--start-hammerspoon` enables its startup fixture.
It skips by default and refuses to start if Hammerspoon is already running.

Use disposable Chrome and Cursor fields to check partial-word expansion, unchanged surrounding text, an emoji prefix, and cursor placement between tags.
Check literal insertion and menu focus in both apps and an empty Ghostty terminal.
Check that Ghostty tag editing and secure fields reject the action without changing text.
