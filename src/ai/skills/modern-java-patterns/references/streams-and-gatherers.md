# Streams and gatherers

Replace imperative loops — `continue`/`break`, nested `if` filtering, manual accumulation into a mutable list — with a stream pipeline.
Stream basics (`map`/`filter`/`reduce`/`collect`) have been stable since JDK 8; `Stream.toList()` is a later convenience, stable since JDK 16. Both apply at every milestone in this skill's scope.
For stateful operations a plain stream cannot express — windowing, fold, scan — use a Gatherer.
Gatherers (`java.util.stream.Gatherers`) reached general availability in JDK 24 (JEP 485), which is stable under this skill's JDK 25 LTS milestone.

## Before/after: manual windowing

Imperative, with a hand-rolled accumulator and nested loop:

```java
List<Double> movingAverages = new ArrayList<>();
for (int i = 0; i <= readings.size() - windowSize; i++) {
    double sum = 0;
    for (int j = i; j < i + windowSize; j++) {
        sum += readings.get(j);
    }
    movingAverages.add(sum / windowSize);
}
```

Modern, JDK 25 (Gatherers stable; needs JDK 24+):

```java
List<Double> movingAverages = readings.stream()
    .gather(Gatherers.windowSliding(windowSize))
    .map(window -> window.stream().mapToDouble(Double::doubleValue).average().orElseThrow())
    .toList();
```

## Quick reference

| Imperative shape | Stream/Gatherer replacement | Min JDK |
|---|---|---|
| Nested `if` filtering into a mutable list | `.filter(...).map(...).toList()` | 16 (`.filter`/`.map` are JDK 8; `.toList()` is JDK 16) |
| Manual sliding/fixed window accumulation | `Gatherers.windowSliding` / `Gatherers.windowFixed` | 24 (stable at 25) |
| Manual running-total accumulation | `Gatherers.fold` | 24 (stable at 25) |
