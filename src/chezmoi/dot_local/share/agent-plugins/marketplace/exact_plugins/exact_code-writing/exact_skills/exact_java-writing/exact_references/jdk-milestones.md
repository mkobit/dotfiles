# JDK version-safety table

Status: not available, preview (`--enable-preview`, API not guaranteed stable), stable, withdrawn (never use).

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

String templates were previewed in JDK 21–22 and withdrawn before JDK 23 shipped.
Do not recommend them.
Use `String.format`, `StringBuilder`, or text blocks instead.

## Preview caution: structured concurrency

Structured concurrency (JEP 505) is still preview at JDK 25; its API shape changed between JDK 21 and 25 previews.
Mark any `StructuredTaskScope` code sample as preview and do not present it with the same confidence as stable features.
