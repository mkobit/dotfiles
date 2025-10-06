---
description: Batch organize and transform multiple vault files or folders
argument-hint: <@folder or @file1 @file2 ...> [vault-path]
---

Batch process multiple files or entire folders, applying transformation and organization conventions to bring messy content into vault standards.

## What this does

This command applies `/obsidian-transform` logic to multiple files at once:
- Clean up messy folders with inconsistent formatting
- Batch transform imported content
- Reorganize existing Area/Meta structure
- Apply vault conventions to legacy notes

**Note:** This command can call `/obsidian-transform` for individual files if needed.

## Workflow

1. **Detect vault root** - Find `.obsidian/` directory (use provided vault-path or search from current directory)
2. **Identify targets** - List all files to process
3. **Research patterns** - Understand existing vault conventions (tags, properties, structures)
4. **Process each file** - Transform content following vault standards
5. **Report** - Summarize changes made

## Vault conventions

### File naming
- **Sentence case** - Capitalize first word only
- **Temporal prefixes** - ISO 8601 `yyyy-MM-ddTHH-mm-ss` format (local time)
  - Example: `2025-10-05T14-30-45 Project name.md`
  - Exception: Daily notes use `yyyy-MM-dd` only
- **Identity files** - Timestamp + name: `2025-01-22T19-45-00 Name.md`, add to `aliases` property

### Property conventions
**Property types must be consistent across entire vault.** Research existing properties before creating new ones.

- **Lowercase** except proper nouns and acronyms
- **Forward slash notation** for grouping: `media/author`, `family/sibling`, `location/hometown`
- **Semantic specificity** - Descriptive names that convey exact meaning
- **NO generic link properties** - Never `internal link/related`; embed wikilinks naturally in content
- **Date/time format** - ISO 8601 in local time: `yyyy-MM-ddTHH:mm:ss` or `yyyy-MM-dd`
- **Pragmatic approach** - Use many properties initially, consolidate later as patterns emerge

Examples: `family/mother: [[Mom]]`, `mentor/advisor: [[Name]]`, `media/author: [[Author]]`

### Tagging system
**Maximum depth: 3 levels** using forward slash notation.

Tags are **dimensional and categorical grouping mechanisms**:
- **Organizational units** - Group and categorize content
- **Common across files** - Shared by multiple notes, not unique
- **NO identity tags** - Never `#characters/Name`; use properties/wikilinks instead

Common top-level: `#project`, `#meta`, `#note`, `#identity`, `#career`, `#software`

Good: `#software/programming/devex`
Bad: `#software/programming/devex/tooling` (4 levels)

Research existing tags before creating new ones to avoid sprawl.

### Writing style
- **Personal and informal** - Natural, conversational style
- **Factual and evidence-based** - Record what was said/done, no interpretation or marketing speak
- **No fluff** - Remove promotional language, superlatives, unnecessary elaboration
- **Extreme conciseness** - Low verbosity
- **One sentence per line** - For better version control
- **Link-heavy** - Extensively use `[[wikilinks]]` to related concepts
- **Sentence case headings** - Capitalize first word only
- **Emoji section headers** - `⚡ Overview`, `🔗 References`, `📋 Details`, `🎯 Goals`, `📝 Notes`

### Content transformation rules
When processing raw content:
1. **Extract key information** - Identify main concepts and facts
2. **Remove verbosity** - Strip fluff, marketing language, filler words
3. **Structure logically** - Use headings, one sentence per line
4. **Add wikilinks** - Link to related concepts (research vault first for existing notes)
5. **Split if needed** - Create atomic notes (one main concept per file) with wikilinks between them
6. **Apply frontmatter** - Add properties and tags following vault conventions

### Wikilinks
- Internal links: `[[filename]]`
- Display text: `[[filename|display text]]` - use `|` for friendly names
- Embed notes: `![[filename]]`
- For timestamped files: `[[2025-10-01T12-15-12 Movie Title|Movie Title]]`
- Block anchors: `[[filename#^blockid]]` - prefer over section anchors
- Create human-readable block IDs: ` ^quote-of-the-day` at end of paragraph

## Execution steps

1. **Research vault patterns**
   - Find `.obsidian/` directory to identify vault root
   - Grep for existing properties to understand types and naming conventions
   - Grep for existing tags to understand taxonomy
   - Look for similar notes to understand structure patterns

2. **Identify files to process**
   - If folder: recursively find all `.md` files
   - If multiple files: validate they all exist
   - Show list and ask for confirmation if processing >10 files

3. **Process each file**
   - Read current content
   - Analyze and transform following conventions
   - Update or create new file with proper naming
   - Track original → new file mappings
   - Update wikilinks if files renamed

4. **Handle reorganization**
   - Move files to appropriate Area/Meta locations if needed
   - Update all backlinks across vault when files move
   - Archive or remove source files if transformed into new locations

5. **Validate**
   - Verify all new files created successfully
   - Check frontmatter is valid YAML
   - Confirm property types match vault conventions
   - Ensure tag hierarchy doesn't exceed 3 levels
   - Validate wikilinks aren't broken

6. **Report**
   - Summary: X files processed, Y created, Z renamed/moved
   - List all transformations made
   - Show any files that need manual review
   - Highlight any wikilink updates made

## Important notes

- **Atomic notes** - Prefer multiple small focused files over large documents
- **Research first** - Always understand existing patterns before creating new conventions
- **Area/Meta organization** - Most content goes into Area/ or Meta/ subdirectories
- **Be decisive** - Apply conventions autonomously; aim for 98% automation
- **Preserve meaning** - Remove fluff but keep all factual information
- **Link extensively** - Rich wikilink networks are core to vault value
- **Backup consideration** - For large batch operations, suggest user review git status first
- **Can call other commands** - Use `/obsidian-transform` for individual file processing if helpful
