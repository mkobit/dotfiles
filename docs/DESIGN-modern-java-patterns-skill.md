# Modern java patterns skill design

## Problem
Java training data overrepresents imperative style.
For/while loops with `continue`/`break`, deeply nested `if` chains, manual `instanceof`-and-cast, hand-rolled thread pools, and index-based collection access all dominate what coding models have seen.
Modern JDK releases, spanning the three LTS milestones 17/21/25, replaced most of these idioms with more concise, safer alternatives.
Coding agents default to the imperative style anyway, even on codebases that target JDK 21 or 25.
This skill exists to correct that default by giving agents a concrete map from imperative pattern to modern replacement, gated by the JDK version each replacement actually requires.

## Non-goals
No Spring Boot or other application framework guidance — this skill covers core JDK language/API features plus a small set of widely-used, non-framework immutability libraries (Guava, AutoValue), not full frameworks.
No coverage of JDK versions below 17.
No recommendation of string templates.
String templates were previewed in JDK 21 and JDK 22, then withdrawn before reaching general availability, and must not appear in this skill's guidance.
No firm recommendation of structured concurrency as if it were stable: it is still in preview as of JDK 25 (fifth preview, JEP 505; not expected to finalize before JDK 27). It stays in scope but is marked preview-only, distinctly from the stable virtual-threads content it sits alongside — see virtual-threads-and-structured-concurrency.md below.

## Scope
Three LTS milestones only: JDK 17, JDK 21, JDK 25.
Intermediate non-LTS releases (18 through 20, 22 through 24) are referenced only to note when a feature entered preview or reached general availability, since each LTS release inherits everything finalized in the non-LTS releases before it.
Non-LTS releases are not adoption targets on their own.

## Skill structure
```
src/ai/skills/modern-java-patterns/
  SKILL.md                                           # short router: symptom -> feature -> min JDK -> reference file
  references/jdk-milestones.md                       # version-safety table; explicit string-templates exclusion
  references/streams-and-gatherers.md                # primary: loops/continue/break/nested-if -> Stream pipelines + Gatherers
  references/pattern-matching-and-records.md         # records, sealed types, pattern matching for instanceof/switch
  references/immutability-and-value-types.md         # records + Guava Immutable* + AutoValue, favor-when-available
  references/virtual-threads-and-structured-concurrency.md
  references/sequenced-collections.md
```
This follows the existing heavy-reference skill pattern already deployed in this repo's own `skills.toml` — for example `wshobson-llm-finetuning`'s `lora-qlora-recipes` skill (`references/hyperparameters.md`, `references/unsloth-trl-mapping.md`) and `wshobson-llm-application-dev`'s `prompt-engineering-patterns` skill, both `"present"` today, ship a `references/` subdirectory alongside a short `SKILL.md`.
Nested paths deploy automatically: `.chezmoiexternals/ai-authored-skills.toml.tmpl` globs every file under a skill's directory and preserves relative paths, so `references/*.md` needs no template changes.
This is the first *authored* skill (as opposed to upstream-sourced) to use a nested `references/` directory — both existing authored skills (`technical-writing`, `write-agent-context`) are flat single files — so the implementer should confirm the nested paths in `chezmoi diff` output rather than assume it's proven by precedent.

## SKILL.md content
Frontmatter `description` follows this repo's own authored-skill convention rather than importing a generic external template: lead with a verb describing what the skill does, with "use when ..." as a trailing clause naming concrete symptoms (matches `write-agent-context`'s and `technical-writing`'s existing phrasing, not the "starts with Use when" template from the `writing-skills` skill). Symptoms named: manual `instanceof`/cast chains, null-check ladders, hand-rolled POJOs and defensive-copy/builder boilerplate, manual `ExecutorService`/`Future` management, index-based first/last collection access, and loops accumulating state that a stream pipeline or gatherer could express directly.
Body is a quick-reference table: symptom, modern feature, minimum stable JDK, which reference file to read.
Streams-and-gatherers is listed first since it addresses the most common imperative pattern (loops and nested conditionals).
An explicit boundary line states this skill does not cover Spring or other frameworks, and does not apply to codebases pinned below JDK 17.

## Reference file contents

### jdk-milestones.md
A table with one row per feature area, columns for JDK 17 / 21 / 25 status (absent, preview, stable).
Includes an explicit "do not use" row for string templates, with the reason (withdrawn, never GA).
Exact JEP numbers get verified against openjdk.org/jeps during implementation rather than asserted from memory here.

### streams-and-gatherers.md
Stream pipeline basics (`map`/`filter`/`reduce`/`collect`, `Stream.toList()`) as the default replacement for imperative loops with `continue`/`break` and nested `if` filtering.
Gatherers (`java.util.stream.Gatherers`) for the stateful cases plain streams cannot express: windowing (fixed and sliding), fold, scan, and similar custom intermediate operations that today get hand-rolled as loops with mutable accumulators.
Gatherers reached general availability in JDK 24, which is stable under this skill's JDK 25 LTS milestone.
One before/after example: a loop with a mutable accumulator and manual windowing logic, rewritten with `Gatherers.windowSliding` or an equivalent.

### pattern-matching-and-records.md
Records, sealed classes/interfaces, pattern matching for `instanceof`, pattern matching for `switch` including `case null` handling, record patterns.
One before/after example: an `instanceof`-and-cast chain rewritten as a pattern-matched `switch` expression.

### immutability-and-value-types.md
Records as the default immutable value type (JDK-native, always available, stable since 17).
When Guava is already a project dependency, favor its `ImmutableList`/`ImmutableMap`/`ImmutableSet` over `Collections.unmodifiableX()` or manual defensive copies.
When AutoValue is already a project dependency, favor `@AutoValue` for value types that need generated builders or validation beyond what a plain record gives you.
Both library recommendations are conditional on the library already being present — this file states the JDK-only fallback in the same breath as the library recommendation, never as a separate path to hunt for.
This favor-when-available framing is scoped to this file only; other reference files stay JDK-only unless a future revision extends it deliberately.
A small number of before/after examples (not exhaustive per library) given the emphasis on lean examples over coverage.

### virtual-threads-and-structured-concurrency.md
Virtual threads: stable since JDK 21, presented as the default concurrency recommendation without caveats.
Structured concurrency and scoped values: scoped values are stable since JDK 25 (JEP 506); structured concurrency is still preview as of JDK 25 (fifth preview, JEP 505) despite being significantly more battle-tested in design and scope than a feature like string templates ever was.
Structured concurrency content is visually and textually distinct from the stable virtual-threads content in the same file — marked preview, `--enable-preview`-required, and subject to API changes across previews (its shape has already changed between the JDK 21 and JDK 25 previews) — rather than presented with the same confidence as the stable material.
One before/after example: manual `ExecutorService` plus `Future` plus `try`/`finally` shutdown, rewritten with virtual threads directly; structured concurrency shown as a preview-flagged extension of that same example, not a separate stable recommendation.

### sequenced-collections.md
`SequencedCollection`, `SequencedSet`, `SequencedMap`; `getFirst()`/`getLast()`/`reversed()`.
One before/after example: index-based first/last element access rewritten using the sequenced-collection methods.

## Deployment
Add one entry to `src/chezmoi/.chezmoidata/ai/skills/authored.toml` under `[ai.skills.authored]`:
```toml
modern-java-patterns = "present"
```
`"present"` deploys to every tool's skill directory (Claude, antigravity, cursor, codex), matching the existing authored skills.
No changes needed to `.chezmoiexternals/ai-authored-skills.toml.tmpl` or any `.chezmoiremove.tmpl` file.
Preview with `chezmoi diff`, apply with `chezmoi apply`.

## Testing approach
This is a recognition/pattern skill, not a discipline-enforcing rule skill, so the full adversarial pressure-scenario RED-GREEN-REFACTOR loop from the writing-skills process does not apply.
Test as application scenarios instead: give a subagent an imperative Java snippet with no skill loaded and record the baseline (does it reach for the old idiom?).
Then repeat with the skill available and verify it recognizes the modern replacement, cites the correct minimum JDK, and does not recommend string templates.
Cover at least one scenario per reference file: a loop-with-accumulator case for streams-and-gatherers, an `instanceof`-chain case for pattern-matching-and-records, a hand-rolled-builder or defensive-copy case for immutability-and-value-types (both with and without Guava/AutoValue on the classpath, to verify the fallback framing actually holds), a manual-executor case for virtual-threads-and-structured-concurrency (verify virtual-threads guidance stays unconditional while structured-concurrency guidance stays marked preview), and an index-based-access case for sequenced-collections.
