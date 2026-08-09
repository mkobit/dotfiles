# Functional style in src/python

Detail for the "Coding style" preference in [AGENTS.md](AGENTS.md).
Prefer functional, declarative code over imperative accumulation and mutation — matched against the surrounding code's idiom, not forced where it hurts clarity.

## Building collections

Prefer a comprehension, a generator, or filtering a pre-built sequence over appending inside a loop.

Bad:
```python
results = []
if condition_a:
    results.append("a")
if condition_b:
    results.append("b")
```

Better:
```python
items = ["a" if condition_a else None, "b" if condition_b else None]
results = [item for item in items if item is not None]


def get_results() -> Iterator[str]:
    if condition_a:
        yield "a"
    if condition_b:
        yield "b"
```

Reach for `list.append()` in a loop when the accumulation genuinely depends on prior iterations and a comprehension would obscure that.

## Parameter types

Prefer `Sequence`, `Iterable`, or `Mapping` over `list`/`dict` for parameters the function only reads.
It documents that the callee won't mutate the argument.

```python
from collections.abc import Sequence


def process_data(items: Sequence[str]) -> Sequence[str]: ...
```

## Reassignment and string building

Prefer expressing a value once (ternary, f-string, `"".join(...)`) over reassigning a variable or concatenating a string incrementally.

Bad:
```python
message = "Hello"
if condition:
    message += ", User"
else:
    message += ", Guest"
```

Better:
```python
name = "User" if condition else "Guest"
message = f"Hello, {name}"
```

## Deduplication

`dict.fromkeys()` preserves order and reads more directly than a `seen`-set loop:
```python
ordered = list(dict.fromkeys(reversed(items)))
```
