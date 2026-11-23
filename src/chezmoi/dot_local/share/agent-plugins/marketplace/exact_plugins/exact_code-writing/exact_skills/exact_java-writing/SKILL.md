---
name: java-writing
description: Write and modernize Java 17/21/25+ code using records, sealed types, pattern matching, virtual threads, streams/Gatherers, sequenced collections, and Guava/AutoValue when already a dependency. Replaces imperative instanceof/cast chains, null-check ladders, hand-rolled POJOs and defensive copies, manual ExecutorService/Future, index-based collection access, and mutable-accumulator loops. Not for Spring or framework conventions; not for codebases below JDK 17.
---

# Java writing

Guides writing new Java 17/21/25+ code and modernizing imperative Java symptoms, gated by minimum JDK version.

## Quick reference

| Symptom | Modern feature | Min stable JDK | Reference |
|---|---|---|---|
| Loops with `continue`/`break`, nested `if` filtering, manual accumulation | Stream pipelines; Gatherers for stateful/windowed cases | 8 (streams); 25 (Gatherers) | [streams-and-gatherers.md](references/streams-and-gatherers.md) |
| `instanceof`-and-cast chains, type-switch ladders | Sealed types + pattern matching for `instanceof`/`switch`, record patterns | 17 (`instanceof`); 21 (`switch`, record patterns) | [pattern-matching-and-records.md](references/pattern-matching-and-records.md) |
| Hand-rolled POJOs, defensive copies, manual builders | Records; Guava `Immutable*`/`@AutoValue` when already a dependency | 17 | [immutability-and-value-types.md](references/immutability-and-value-types.md) |
| Manual `ExecutorService`/`Future`/shutdown management | Virtual threads (stable); structured concurrency (preview) | 21 (virtual threads); preview at 25 (structured concurrency) | [virtual-threads-and-structured-concurrency.md](references/virtual-threads-and-structured-concurrency.md) |
| Index-based first/last element access, manual reversal | `SequencedCollection`/`SequencedMap` | 21 | [sequenced-collections.md](references/sequenced-collections.md) |

See [jdk-milestones.md](references/jdk-milestones.md) for the full version-safety table, including features this skill explicitly excludes.

## Boundaries

Not for Spring Boot or other application frameworks — core JDK and the two named libraries (Guava, AutoValue) only.
Not for codebases pinned below JDK 17.
Never recommend string templates: previewed in JDK 21/22, withdrawn, never reached general availability.
