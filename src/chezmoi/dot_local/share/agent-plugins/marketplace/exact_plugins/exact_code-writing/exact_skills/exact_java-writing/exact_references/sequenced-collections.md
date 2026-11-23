# Sequenced collections

Replace index-based first/last element access and manual reversal with the sequenced-collection methods.
`SequencedCollection`, `SequencedSet`, and `SequencedMap` have been stable since JDK 21.

## Before/after: first/last access and reversal

Imperative:

```java
String first = list.isEmpty() ? null : list.get(0);
String last = list.isEmpty() ? null : list.get(list.size() - 1);
List<String> reversed = new ArrayList<>(list);
Collections.reverse(reversed);
```

Modern, JDK 21+:

```java
String first = list.isEmpty() ? null : list.getFirst();
String last = list.isEmpty() ? null : list.getLast();
List<String> reversed = list.reversed();
```

`reversed()` returns a view backed by the original collection, not a copy.
Mutating the view mutates the original, and vice versa — this is a correctness difference from `Collections.reverse`, not just a syntax change.

## Quick reference

| Imperative shape | Replacement | Min JDK |
|---|---|---|
| `list.get(0)` / `list.get(size - 1)` | `list.getFirst()` / `list.getLast()` | 21 |
| Manual `Collections.reverse` into a copy | `list.reversed()` (a view, not a copy) | 21 |
