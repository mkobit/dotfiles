# Immutability and value types

Replace hand-rolled POJOs, manual defensive copies, and hand-rolled builders with immutable value types.
Records are the default.
Guava and AutoValue are recommended only when already a project dependency — each note below states the JDK-only fallback, so the guidance holds when the library is absent.

## Before/after: defensive copies

Imperative, with a manual defensive copy on the way in and out:

```java
final class Config {
    private final List<String> tags;
    Config(List<String> tags) {
        this.tags = new ArrayList<>(tags);
    }
    List<String> getTags() {
        return Collections.unmodifiableList(tags);
    }
}
```

Modern, JDK 17+ (a record's canonical constructor normalizes the field once):

```java
record Config(List<String> tags) {
    Config {
        tags = List.copyOf(tags);
    }
}
```

## If Guava is already a dependency

Prefer `ImmutableList.copyOf(tags)` (or `ImmutableMap`/`ImmutableSet`) over `List.copyOf(tags)` in the example above.
If Guava is not a dependency, `List.copyOf()` (JDK 10+) is the no-dependency equivalent — do not add Guava solely for this.

## If AutoValue is already a dependency

Prefer `@AutoValue` over a hand-rolled builder for a value type that needs a generated builder (many optional fields) or shared validation across multiple construction paths.
If AutoValue is not a dependency, use a record's canonical constructor for simple validation, or a plain nested builder class when many optional fields are unavoidable — do not add AutoValue solely for this.

## Quick reference

| Imperative shape | Replacement | Condition |
|---|---|---|
| Hand-rolled POJO with manual `equals`/`hashCode`/`toString` | Record | JDK 17+, always |
| Manual defensive copy in and out | `List.copyOf()` / `ImmutableList.copyOf()` | JDK-only, or Guava if present |
| Hand-rolled builder for many optional fields | `@AutoValue` builder | Only if AutoValue already a dependency |
