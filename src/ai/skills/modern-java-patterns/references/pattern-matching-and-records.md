# Pattern matching and records

Replace `instanceof`-and-cast chains and type-switch ladders with sealed types and pattern matching.
Records and pattern matching for `instanceof` have been stable since JDK 17.
Pattern matching for `switch` and record patterns have been stable since JDK 21, including `case null` handling that replaces a leading defensive null check.

## Before/after: instanceof-and-cast chain

Imperative:

```java
String describe(Object shape) {
    if (shape instanceof Circle) {
        Circle c = (Circle) shape;
        return "Circle radius=" + c.radius();
    } else if (shape instanceof Rectangle) {
        Rectangle r = (Rectangle) shape;
        return "Rectangle " + r.width() + "x" + r.height();
    } else {
        return "Unknown shape";
    }
}
```

Modern, JDK 21+ (sealed types make the switch exhaustive, so there is no reachable "unknown shape" case):

```java
sealed interface Shape permits Circle, Rectangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double width, double height) implements Shape {}

String describe(Shape shape) {
    return switch (shape) {
        case Circle c -> "Circle radius=" + c.radius();
        case Rectangle r -> "Rectangle " + r.width() + "x" + r.height();
    };
}
```

## Quick reference

| Imperative shape | Replacement | Min JDK |
|---|---|---|
| `if (x instanceof T) { T t = (T) x; ... }` | `if (x instanceof T t) { ... }` | 17 |
| `if (x == null) return ...;` inside a switch-like chain | `case null ->` in a pattern-matched `switch` | 21 |
| Type-switch ladder over a closed set of subtypes | Sealed interface/class + pattern-matched `switch` | 21 (17 for sealed alone) |
