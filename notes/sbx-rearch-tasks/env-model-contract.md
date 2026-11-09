# Environment model selection limits

Installed SBX `0.50.1` rejects model/provider fields at the environment root and under `sandboxOptions`.
It also rejects `--model` and `--provider` on `env run` and `env exec`.
Do not generate those fields or flags.

Native `sbx run` accepts model/provider selection for supported built-in local agents and supports tracked v2 mixins through `--kit`.
That syntax does not prove an equivalent route for a repository environment's secrets, ports, lifecycle, and clone metadata.
No model lifecycle test or live setting mutation was performed in this investigation.

Task 7 must retain the tracked environment route for ordinary hosted execution.
A requested local-model route must stop before claim until its supported lifecycle preserves the complete kit, toolchain, clone identity, and return remote.
A capable machine must test that route after normal Chezmoi apply enables the declared feature and an Ollama service/model is available.
The work machine can implement offline validation and rejection cases; it cannot establish native lifecycle acceptance.

Primary sources: [environment fields](https://docs.docker.com/ai/sandboxes/configuration/environment-files/#sandboxoptions), [model selection](https://docs.docker.com/ai/sandboxes/configuration/models/), and [native run options](https://docs.docker.com/reference/cli/sbx/run/).
Detailed local evidence: `/tmp/sbx-rearch-env-model-contract.md`.
