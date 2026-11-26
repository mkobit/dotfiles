# Review dotfiles sessions for skill evals

The Codex project hook samples about one in ten dotfiles sessions when they end.
It hashes the session ID, so resuming the same session keeps the same sample decision.
The hook stores the Codex session ID as an empty local directory.
The transcript stays in Codex session storage.

## Enable capture

Use a trusted personal checkout and start Codex from the dotfiles checkout,
a linked worktree, or a directory inside either checkout.
The source directory from `chezmoi cd` also works.
For a linked worktree, update the main checkout so Codex can find the hook.
The linked worktree must also contain the review script.

```sh
CHEZMOI_ENABLE_PERSONAL_SESSION_EVAL_CAPTURE=1 codex --no-daemon
```

Review and trust the project hook in `/hooks` the first time.
The `--no-daemon` option lets the hook use the opt-in from this launch.
Leave the variable unset in overlays and other shells that must not sample sessions.

Codex calls the hook when the session ends.
A single assistant reply or a switch to a different thread does not necessarily end the session.
The pending markers live in `${XDG_STATE_HOME:-~/.local/state}/chezmoi-session-eval/codex/`.
Use the same state directory when you run the hook and review command.
[Codex hook events and trust](https://learn.chatgpt.com/docs/hooks#sessionend)

## Review a sample

From the dotfiles Git root, run:

```sh
scripts/review-chezmoi-session.py
```

The command looks for the `chezmoi-skills` checkout under `~/workspace/mkobit/`.
Set `CHEZMOI_SKILLS_CHECKOUT` to the checkout path if it is elsewhere.
Trust the destination checkout in Codex.
The checkout must contain the `session-eval-review` skill from the latest `chezmoi-skills` checkout.

Enter `y` to open a native Codex fork in that checkout.
The fork uses the skill to draft a redacted eval candidate for review.
Press Enter to leave the session pending, or enter `s` to skip it.
A successful Codex fork command marks the sample as handled.

If Codex cannot open the fork, the sample stays pending.
To retry an archived session, run `codex unarchive <session-id>` first.
Skip the sample if the source session is unavailable.
