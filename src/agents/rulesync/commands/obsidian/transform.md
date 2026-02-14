---
description: Transform raw content into clean, organized Obsidian vault notes
targets: ["*"]
argument-hint: <@file or raw text> [vault-path]
---

Transform raw content (voice transcriptions, quick notes, pastes) into clean, organized markdown notes following Obsidian vault conventions.

## Workflow

1. **Detect vault root** - Find `.obsidian/` directory (use provided vault-path or search from current directory)
2. **Research patterns** - Use Glob/Grep to understand existing tags, properties, note structures
3. **Transform content** - Clean, restructure, and enrich the content
4. **Create notes** - Write atomic notes with proper naming and frontmatter
5. **Report** - Show what was created and where

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

2. **Analyze content**
   - Identify main concepts (potential note splits)
   - Extract key facts and information
   - Identify potential wikilinks (people, places, concepts)
   - Determine appropriate tags and properties

3. **Transform and create**
   - Generate ISO 8601 timestamp: `yyyy-MM-ddTHH-mm-ss`
   - Create atomic note files with proper naming
   - Write frontmatter with consistent property types
   - Format content: one sentence per line, remove fluff, add wikilinks
   - Use emoji section headers where appropriate

4. **Validate**
   - Verify files created in vault
   - Confirm frontmatter is valid YAML
   - Check that property types match vault conventions
   - Ensure tag hierarchy doesn't exceed 3 levels

5. **Report**
   - List files created with paths
   - Show key transformations made
   - Highlight any decisions requiring user review

## Important notes

- **Atomic notes** - Prefer multiple small focused files over large documents
- **Research first** - Always understand existing patterns before creating new conventions
- **Area/Meta organization** - Most content goes into Area/ or Meta/ subdirectories
- **Be decisive** - Apply conventions autonomously; aim for 98% automation
- **Preserve meaning** - Remove fluff but keep all factual information
- **Link extensively** - Rich wikilink networks are core to vault value
