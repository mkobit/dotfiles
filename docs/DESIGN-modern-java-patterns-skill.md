# Modern java patterns skill design

## Problem
Java training data overrepresents imperative style.
For/while loops with `continue`/`break`, deeply nested `if` chains, manual `instanceof`-and-cast, hand-rolled thread pools, and index-based collection access all dominate what coding models have seen.
Modern JDK releases (17 through 25, all LTS) replaced most of these idioms with more concise, safer alternatives.
Coding agents default to the imperative style anyway, even on codebases that target JDK 21 or 25.
This skill exists to correct that default by giving agents a concrete map from imperative pattern to modern replacement, gated by the JDK version each replacement actually requires.

## Non-goals
No Spring Boot or other framework-specific guidance — this skill covers core JDK language and API features only.
No coverage of JDK versions below 17.
No recommendation of string templates.
String templates were previewed in JDK 21 and JDK 22, then withdrawn before reaching general availability, and must not appear in this skill's guidance.

## Scope
Three LTS milestones only: JDK 17, JDK 21, JDK 25.
Intermediate non-LTS releases (18 through 20, 22 through 24) are referenced only to note when a feature entered preview or reached general availability, since each LTS release inherits everything finalized in the non-LTS releases before it.
Non-LTS releases are not adoption targets on their own.

## Skill structure
```
src/ai/skills/modern-java-patterns/
  SKILL.md                                          # short router: symptom -> feature -> min JDK -> reference file
  references/jdk-milestones.md                      # version-safety table; explicit string-templates exclusion
  references/streams-and-gatherers.md                # primary: loops/continue/break/nested-if -> Stream pipelines + Gatherers
  references/pattern-matching-and-records.md         # records, sealed types, pattern matching for instanceof/switch
  references/virtual-threads-and-structured-concurrency.md
  references/sequenced-collections.md
```
This follows the existing heavy-reference skill pattern already used by upstream skills in this repo (for example the `javascript-typescript` plugin's `modern-javascript-patterns` and `nodejs-backend-patterns` skills, which each ship a `references/` subdirectory alongside a short `SKILL.md`).
Nested paths deploy automatically: `.chezmoiexternals/ai-authored-skills.toml.tmpl` globs every file under a skill's directory and preserves relative paths, so `references/*.md` needs no template changes.

## SKILL.md content
Frontmatter `description` starts with "Use when..." and names concrete symptoms: manual `instanceof`/cast chains, null-check ladders, hand-rolled POJOs, manual `ExecutorService`/`Future` management, index-based first/last collection access, and loops accumulating state that a stream pipeline or gatherer could express directly.
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

### virtual-threads-and-structured-concurrency.md
Virtual threads (stable in JDK 21), structured concurrency and scoped values (preview starting JDK 21, stable in JDK 25).
One before/after example: manual `ExecutorService` plus `Future` plus `try`/`finally` shutdown, rewritten with `StructuredTaskScope`.

### sequenced-collections.md
`SequencedCollection`, `SequencedSet`, `SequencedMap`; `getFirst()`/`getLast()`/`reversed()`.
One before/after example: index-based first/last element access rewritten using the sequenced-collection methods.

## Deployment
Add one entry to `src/chezmoi/.chezmoidata/ai/skills.toml` under `[ai.skills.authored]`:
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
Cover at least one scenario per reference file: a loop-with-accumulator case for streams-and-gatherers, an `instanceof`-chain case for pattern-matching-and-records, a manual-executor case for virtual-threads-and-structured-concurrency, and an index-based-access case for sequenced-collections.
