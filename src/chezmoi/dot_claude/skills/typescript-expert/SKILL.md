---
name: TypeScript Code Expert
description: Enforces functional programming, immutability, and strict type safety when writing, reviewing, or editing TypeScript and React code.
---

# TypeScript Code Expert Guidelines

Follow these guidelines when writing TypeScript.
Apply these rules strictly for new code.
Apply these rules pragmatically for existing codebases.

## Functional Programming
Prefer functional programming paradigms over imperative code.
Prefer pure functions.
Avoid side effects.
Use libraries like `remeda`, `fp-ts`, or `lodash-fp` for data transformations.
Prefer these libraries over manual imperative loops.
Use iterator helpers like `.values()` where available in modern environments.
Avoid `class` definitions when possible.
Use classes only when required by frameworks (e.g., Obsidian plugins).
Use classes only when required by third-party library constraints.
Do not use `let` or `var` unless absolutely necessary.
Use `const` for all variable declarations.

## Immutability
Treat all data as immutable by default.
Prefer `readonly` properties in interfaces.
Prefer `ReadonlyArray<T>` over mutable arrays.
Use the spread operator or functional utilities to update state.
Inspect any use of mutable state carefully.
Justify any deviation from immutability.

## Type System
Must not use the `any` type.
Must not use hard type assertions (e.g., `as Type`).
Use `unknown` if the type is not yet known.
Use Zod for runtime validation.
Use generated types for GraphQL or API schemas.
Use Discriminated Unions for modeling state with multiple variations.
Leverage utility types like `Pick`, `Omit`, and `Partial`.
Prefer `interface` for public API definitions.
Prefer `type` for unions and intersections.

## React Guidelines
Use Functional Components.
Use Hooks for state and side effects.
Must not use Class Components.
Decompose complex components into smaller, focused components.
Extract complex logic into custom hooks.
Use strict dependency arrays in `useEffect` and `useCallback`.
Avoid inline function definitions in render if they cause performance issues.
Prefer derived state calculation during render over `useEffect` synchronization.
