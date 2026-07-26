# JDK version-safety table

One row per feature area.
Status is one of: not available, preview (requires `--enable-preview`, API not guaranteed stable), stable.

| Feature | JDK 17 | JDK 21 | JDK 25 |
|---|---|---|---|
| Records (JEP 395) | Stable | Stable | Stable |
| Sealed classes/interfaces (JEP 409) | Stable | Stable | Stable |
| Pattern matching for `instanceof` (JEP 394) | Stable | Stable | Stable |
| Pattern matching for `switch`, record patterns (JEP 441, JEP 440) | Not available | Stable | Stable |
| Sequenced collections (JEP 431) | Not available | Stable | Stable |
| Virtual threads (JEP 444) | Not available | Stable | Stable |
| Stream Gatherers (JEP 485, GA'd in JDK 24) | Not available | Not available | Stable |
| Scoped values (JEP 506) | Not available | Preview | Stable |
| Structured concurrency (JEP 505, fifth preview) | Not available | Preview | Preview |
| String templates (JEP 430, JEP 459) | Not available | Preview | Withdrawn |

## Do not use: string templates

String templates were previewed in JDK 21 (JEP 430) and JDK 22 (JEP 459).
A third preview was planned for JDK 23 and then withdrawn before shipping.
The feature never reached general availability and has not returned.
Do not recommend string templates anywhere in this skill.
Use `String.format`, `StringBuilder`, or text blocks instead.

## Preview caution: structured concurrency

Structured concurrency is still preview as of JDK 25 (JEP 505, its fifth preview).
OpenJDK does not expect it to finalize before roughly JDK 27.
Its API shape has already changed across previews — the JDK 21 preview's `ShutdownOnFailure`/`ShutdownOnSuccess` subclasses were replaced by `Joiner`-based construction in JEP 505.
Any code sample using `StructuredTaskScope` must be marked preview and must not be presented with the same confidence as stable features like virtual threads.
See `virtual-threads-and-structured-concurrency.md` for how this distinction is drawn in practice.
