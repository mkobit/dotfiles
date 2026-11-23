# Handoff and isolation protocol

Use this protocol when dispatching a fresh-context subagent to author black-box contract tests.

## Co-located source slicing rules

When public declarations and private implementation bodies share a source file, the parent coordinator reads the file first and extracts only the public signatures, types, and docstrings.
The parent constructs bounded **Allowed Read Slices** pointing to dedicated interface or type files, existing test fixtures, or exact line ranges (`read_file` with `StartLine`/`EndLine` or `sed -n '<start>,<end>p' <file>`) restricted to public declarations.
The parent lists every private implementation body and internal helper range under **Forbidden Implementation Ranges** (`path#L<body_start>-L<body_end>`), or specifies `none (pre-implementation stub)` when authoring contract-first tests before implementation code exists.

## Contract Handoff Payload template

```markdown
### Extracted public signatures and types
- `<path>#L<start>-L<end>`:
```<lang>
<verbatim public signatures and types>
```

### Contract and invariant table
| Case / input | Expected observable outcome | Collection / state inspector | Excluded tautology or internal detail |
|---|---|---|---|
| ... | ... | ... | ... |

### Allowed read slices
- `<test_file_or_fixture_path>` (full file)
- `<source_path>#L<start>-L<end>` (`read_file` with `StartLine`/`EndLine` or `sed -n '<start>,<end>p' <file>`)

### Forbidden implementation ranges
- `<source_path>#L<body_start>-L<body_end>` (or `none (pre-implementation stub)`)
```

## Compile or import failure vs. contract assertion failure

Run test commands with concise traceback flags where supported (for example, `pytest --tb=short` or `--tb=line`) so failing runs do not dump full implementation bodies into the subagent context window.
If a test fails to compile or import, fix test-side syntax, imports, or types using only **Extracted public signatures and types** and **Allowed read slices**.
If a test compiles and executes but fails a contract assertion from the **Contract & Invariant Table** (or fails as expected against a pre-implementation stub), do not read **Forbidden implementation ranges** and do not weaken or alter expected values to match buggy implementation output.
Record the failing contract row in the **Isolation & Coverage Audit** and return control to the parent agent.

## Full-suite verification

Before reporting completion, run the project's test suite command (or the target module's full test command) and report every failing test by name.

## Isolation & Coverage Audit schema

```markdown
### Files and line ranges read
- `<path>#L<start>-L<end>` (confirmed zero overlap with forbidden ranges)

### Invariant-to-table mapping
- Invariant row `<case>` -> `<test_name>` row `<id>` (catches `<production_mutation>`)

### Verification output
- Command: `<exact test command>`
- Status: `<passed / failed>`
- Contract assertion failures for parent remediation: `<none or exact failing row/test names>`
```
