# Local model routing brief

Research date: 2026-11-02.
Scope: task 6 design for SBX, OpenCode, and Pi.
No settings, network rules, environments, or repository files changed.

## Control plane and route contract

Use the established `ai.ollama` keys: `enabled`, `host_url`, `sandbox_url`, and `default_coder_model`.
Use `dig` defaults of `false`, `""`, `""`, and `""`.
An absent or disabled selection does not change existing configuration.
Do not delete providers or restore old defaults when an overlay disables the feature.
Reject an enabled selection with a missing URL or model before any SBX write.
Treat both URL settings as service roots without `/v1`; trim trailing slashes and append `/v1` for compatible APIs.

Use provider ID `ollama` in host OpenCode and Pi.
Use provider ID `ollama-configured` in SBX `model.providers`.
The separate SBX ID avoids unverified precedence against the built-in `ollama` provider and supports a changed host or port.
It describes the configured Ollama route, including a remote LAN server.

| Consumer | Endpoint | Model selection |
| --- | --- | --- |
| Host OpenCode | `host_url` plus `/v1` | `ollama/<default_coder_model>` |
| Host Pi | `host_url` plus `/v1` | Provider `ollama`, model `default_coder_model` |
| Native SBX model service | `host_url` plus `/v1` | Provider `ollama-configured`, model `default_coder_model` |
| Direct guest client | `sandbox_url` plus `/v1` | Repository-owned client configuration |

Task 7 can select `--provider ollama-configured --model <default_coder_model>` for supported native SBX agents.
The persisted provider is `model.providers["ollama-configured"]`.
Do not add another control-plane key for the provider ID.
Do not generate personal guest kits or copy host Pi/OpenCode configuration into guests.

## SBX convergence

Native read-only checks used installed SBX `v0.50.1`, commit `ddb0268d7124b9cf98955d0b08ffd71a0dfcebe4`.
`settings get KEY --json` returns a record whose `value` holds the effective setting.
Verified records were:

```json
{
  "platform.allowExperimentalFeatures": true,
  "feature.model": {"enabled": false, "variant": "", "variantPayload": ""},
  "model.providers": {}
}
```

The platform setting has type `bool`.
The feature and provider settings have type `json`; `feature.model` also has `feature_flag: true`.
Current `run --help` hides model flags while this feature is disabled.
Native `settings set` accepts raw JSON according to the setting type and can reject administrator conflicts.

An ordinary apply hook reads all three records before it writes.
It requires provider `sbx`, a non-`none` SBX installation method, and `ai.ollama.enabled`.
The global task flag `ai.workflow.enabled` does not gate this setup.
It sets the platform boolean only when false.
It copies the feature object and changes only `enabled` to `true`.
It copies the provider map and the existing managed provider object, then sets these owned fields:

```json
{
  "ollama-configured": {
    "url": "<host_url>/v1",
    "wire": "openai",
    "name": "Ollama (configured)"
  }
}
```

Preserve other providers, provider fields, and feature variant metadata.
Compare parsed values before calling `settings set`.
Use an argument array for the serialized JSON.
Malformed records or failed reads prevent writes; failed writes report unmet prerequisites without printing private output.
Correct changed managed values on the next ordinary apply.
Do not use a `run_once` or content-change-only hook for this convergence.

Docker documents both feature gates, host-side Ollama routing, custom endpoint fields, and native support for built-in local Claude Code, Codex, and OpenCode.
Native model selection does not support cloud sandboxes or v3 kits; Pi is outside this documented matrix.
Changing a sandbox model recreates its container, so task 7 must not change an existing model silently.
See [SBX model routing](https://docs.docker.com/ai/sandboxes/configuration/models/).

JSON object settings replace the complete object.
Read, merge, and set are therefore required to retain foreign provider entries.
See [SBX setting update semantics](https://docs.docker.com/ai/sandboxes/configuration/settings/#change-a-setting).

## Host file formats

Extend the existing OpenCode modifier at `src/chezmoi/dot_config/opencode/modify_opencode.json`.
Retain its plugin migration and its tool-install gate.
Merge these owned leaves into the incoming object:

```json
{
  "model": "ollama/<default_coder_model>",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (configured)",
      "options": {"baseURL": "<host_url>/v1"},
      "models": {"<default_coder_model>": {"name": "<default_coder_model>"}}
    }
  }
}
```

Preserve plugins, other providers, other models, existing model metadata, provider options, and unrelated top-level keys.
Do not replace the complete provider object.
See the official [Ollama provider example](https://opencode.ai/docs/providers/#ollama) and [configuration merge rules](https://opencode.ai/docs/config/#locations).

Pi uses `<destination>/.pi/agent/models.json` and `<destination>/.pi/agent/settings.json` by default.
`PI_CODING_AGENT_DIR` can select another agent directory.
Do not create `.config/pi/config.json`.
See [Pi configuration paths](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/configuration.md).

Merge the following provider into `models.json`:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "<host_url>/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "models": [{"id": "<default_coder_model>"}]
    }
  }
}
```

The dummy key is required for model availability and is not a secret.
Preserve foreign providers and provider keys.
Merge the model by its `id` and preserve other model entries and fields.
Do not invent context limits, token limits, or reasoning capabilities.
See [Pi compatible endpoint configuration](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/models.md#configure-a-compatible-endpoint).

Set `defaultProvider: "ollama"` and `defaultModel: "<default_coder_model>"` in Pi `settings.json` while enabled.
Preserve other settings.
Project settings can override these defaults.
See [Pi model settings](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/settings.md#model-and-thinking).

## File ownership and tests

Task 6 owns these bounded changes:

- Extend `dot_config/opencode/modify_opencode.json` and its integration coverage.
- Add `dot_pi/agent/modify_models.json` and `modify_settings.json` as non-executable pure modify templates, without `.tmpl` suffixes.
- Add an ignore gate for both Pi targets when `ai.ollama.enabled` is absent or false, so absent targets are not created as empty objects.
- Add `run_after_08_configure-local-models.sh.tmpl` for native SBX convergence, using the existing Python interpreter resolver for JSON handling.
- Add dedicated render/apply and fake CLI tests in `tests/integration/test_ollama_routing.py`.

Do not modify task 3 hooks `06` and `07`, their policy or secret logic, the installed tools, or guest environment files.
The OpenCode modifier remains ignored when its existing installation gate is off.
Pi has no tool-install selection in the current catalog; do not add one just for configuration.
Use `.chezmoi.destDir` for destination paths and `.chezmoi.sourceDir` for shared templates.

Tests must cover absent and false selections, omitted overlay fields, enabled service roots with trailing slashes, configured models containing colons, foreign provider/model/plugin preservation, and unchanged output on repeated apply.
The fake CLI must return complete native setting records, including feature metadata.
It must reject unexpected commands.
Verify one managed provider update, no write on the second apply, drift repair, preservation of variant fields, and no writes after malformed records or failed reads.
Do not call the network, install Ollama, pull models, or start real SBX environments in these tests.

## Manual prerequisites and limits

The user must have an available Ollama server and the selected model.
The host must reach `host_url`; direct guest clients must reach `sandbox_url` under the repository network policy.
The model must support the tool calls and context length required by the selected agent.
A nondefault `PI_CODING_AGENT_DIR`, invalid existing JSON, or administrator-denied SBX settings require explicit reporting.
No endpoint request or model execution was performed in this research.
The implementation must use ordinary Chezmoi apply for all host settings; no one-off settings commands are required in the handoff.
