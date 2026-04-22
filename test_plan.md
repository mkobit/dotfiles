1. Add `support_kitty_keyboard_protocol false` to `src/chezmoi/dot_config/zellij/config.kdl`.
   - Based on the GitHub issue discussions (specifically zellij issue #3817 and #3540), setting `support_kitty_keyboard_protocol false` in Zellij configuration fixes the problem where Shift+Enter and Ctrl+Enter do not work correctly in certain terminal environments (like when running inside WSL, neovim, or with Claude Code).
2. Complete pre commit steps
   - Complete pre commit steps to make sure proper testing, verifications, reviews and reflections are done.
3. Submit the change.
   - I will submit the change with a descriptive commit message.
