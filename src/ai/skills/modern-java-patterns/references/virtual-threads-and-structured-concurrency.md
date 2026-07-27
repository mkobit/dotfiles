# Virtual threads and structured concurrency

Replace manual `ExecutorService`/`Future`/shutdown management with virtual threads.
Virtual threads (JDK 21+) are stable — use them as the default.
Structured concurrency (JEP 505) is still preview at JDK 25 and is not expected to finalize before roughly JDK 27; do not recommend it with the same confidence as virtual threads.

## Before/after: manual executor management

Imperative:

```java
ExecutorService executor = Executors.newFixedThreadPool(10);
try {
    List<Future<String>> futures = new ArrayList<>();
    for (Request request : requests) {
        futures.add(executor.submit(() -> handle(request)));
    }
    List<String> results = new ArrayList<>();
    for (Future<String> future : futures) {
        results.add(future.get());
    }
    return results;
} finally {
    executor.shutdown();
}
```

Modern, JDK 21+ (virtual threads, stable, no preview flag):

```java
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<String>> futures = requests.stream()
        .map(request -> executor.submit(() -> handle(request)))
        .toList();
    List<String> results = new ArrayList<>();
    for (Future<String> future : futures) {
        results.add(future.get());
    }
    return results;
}
```

### PREVIEW — structured concurrency (JDK 21–25, requires `--enable-preview`)

The API differs from the JDK 21 preview: JEP 505 replaced `ShutdownOnFailure`/`ShutdownOnSuccess` with `Joiner`-based construction, so JDK 21 preview syntax does not carry over to JDK 25.

```java
// PREVIEW: requires --enable-preview; API shape not final, JEP 505 as of JDK 25
try (var scope = StructuredTaskScope.open(Joiner.<String>awaitAll())) {
    List<Subtask<String>> subtasks = requests.stream()
        .map(request -> scope.fork(() -> handle(request)))
        .toList();
    scope.join();
    return subtasks.stream().map(Subtask::get).toList();
}
```

## Quick reference

| Imperative shape | Replacement | Status | Min JDK |
|---|---|---|---|
| Manual `ExecutorService` sizing/pooling | `Executors.newVirtualThreadPerTaskExecutor()` | Stable | 21 |
| Manual `Future` fan-out/fan-in with shared shutdown/error handling | `StructuredTaskScope` | PREVIEW, `--enable-preview` required | 21 (shape changed by 25) |
