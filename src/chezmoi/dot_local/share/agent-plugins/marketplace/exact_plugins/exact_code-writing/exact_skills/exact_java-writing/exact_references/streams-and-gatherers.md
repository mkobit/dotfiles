# Streams and gatherers

Replace imperative loops with a stream pipeline.
For stateful operations a plain stream cannot express — windowing, fold, scan — use a Gatherer (JEP 485, stable since JDK 24).

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
