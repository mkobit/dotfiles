# Data tables and collection inspectors

Use table-driven tests and structural collection inspectors to verify domain contracts without duplicating implementation logic.

## Kotlin (Kotest)

Consolidate case variations into `withData(...)` or `forAll(row(...))` tables and assert collections with `forAll`, `forExactly`, `forAtLeastOne`, or `shouldContainExactlyInAnyOrder`.

```kotlin
forAll(
    row(listOf(100, 200), 300),
    row(emptyList(), 0),
) { amounts, expectedTotal ->
    invoiceTotal(amounts) shouldBe expectedTotal
}
activeUsers(users).shouldContainExactlyInAnyOrder(alice, cara)
```

## Java (JUnit 5 and AssertJ)

Use `@ParameterizedTest` with `@MethodSource` or `@CsvSource` and AssertJ inspectors (`extracting`, `satisfiesExactly`, `satisfiesExactlyInAnyOrder`, `allSatisfy`) instead of index loops (`list.get(0)`).

```java
@ParameterizedTest
@CsvSource({"1000, 3, 334", "900, 3, 300"})
void splitFirstShare(int cents, int shares, int expectedFirst) {
    assertThat(split(cents, shares)).first().isEqualTo(expectedFirst);
}
assertThat(activeUsers(users))
    .extracting(User::name)
    .containsExactlyInAnyOrder("alice", "cara");
```

## Python (pytest)

Use `@pytest.mark.parametrize` with named case IDs and sequence or generator predicate assertions.

```python
@pytest.mark.parametrize(
    ("amounts", "expected_total"),
    [
        pytest.param([100, 200], 300, id="positive_sum"),
        pytest.param([], 0, id="empty_cart"),
    ],
)
def test_invoice_total(amounts, expected_total):
    assert invoice_total(amounts) == expected_total
```

## Go and TypeScript

Use slice-of-struct table tests with `t.Run` in Go and `test.each` with structural array matchers in Vitest or Jest.

```go
for _, tc := range []struct {
    name string
    in   []int
    want int
}{
    {"positive", []int{100, 200}, 300},
    {"empty", nil, 0},
} {
    t.Run(tc.name, func(t *testing.T) {
        if got := InvoiceTotal(tc.in); got != tc.want {
            t.Fatalf("got %d, want %d", got, tc.want)
        }
    })
}
```

## Anti-tautology, mock-boundary, and mutation checklist

- Derive expected values by hand as literals or hand-checked fixtures; never call the code under test or its helpers to compute expectations.
- Exercise real collaborators by default; mock only slow or external boundaries below the side effects the test depends on, mirror complete real data structures in test doubles, never assert on a mock itself, and keep test-only cleanup helpers in test utilities rather than production classes.
- Run a mental mutation check (wrong constant or argument, wrong branch handler, missing state transition, empty or default return, missing zero, empty, nil, or malformed input validation) to confirm at least one table row fails for each realistic production bug.
