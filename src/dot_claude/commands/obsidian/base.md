---
description: Create database queries to search and filter vault notes by properties and tags
argument-hint: <description of query> [--file <output.base>]
---

Generate Obsidian Bases queries using natural language descriptions.

## What is Bases?

Bases is an Obsidian plugin that creates database-like views of your vault notes using properties, tags, and metadata.
Think of it as SQL for your markdown vault - you define filters, formulas, and views to query and display notes matching specific criteria.

Bases queries can be:
- Saved as `.base` files (dedicated database views)
- Embedded inline using ` ```base ` code blocks
- Referenced and embedded in other notes with `![[filename.base]]`

Use Bases when you want to dynamically list/view notes based on their properties (e.g., "all books rated >4 stars", "projects modified this week", "people I contacted recently").

## Workflow

1. **Understand request** - Parse what the user wants to query/view
2. **Research vault** - Find existing properties, tags, and data patterns
3. **Generate query** - Create valid Bases syntax matching vault schema
4. **Output** - Return as code block (for inline use) or write to `.base` file

## Bases syntax reference

### Structure

Bases queries have four main sections:
- **filters** - Narrow which files appear (global or per-view)
- **formulas** - Computed properties accessed as `formula.formulaname`
- **properties** - Define which properties to display
- **views** - Configure how data is displayed (table, cards)

### Property types

- **Note properties**: `propertyname` (from frontmatter)
- **File properties**: `file.name`, `file.mtime`, `file.tags`, `file.path`, `file.folder`, `file.ctime`, `file.links`
- **Formula properties**: `formula.formulaname` (computed from formulas section)

### Filters

Narrow which files appear using boolean logic:

```yaml
filters:
  and:
    - file.hasTag("project")
    - 'status == "active"'
  or:
    - file.inFolder("Area")
    - file.inFolder("Projects")
  not:
    - 'file.ext != "md"'
```

**Conjunctions:**
- `and` - All conditions must be true
- `or` - At least one condition must be true
- `not` - None of the conditions should be true

**Operators:**
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Boolean: `&&`, `||`, `!`
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Date arithmetic: `now() + "1d"`, `file.mtime - "1 week"`, `date("2024-12-01") + "1M"`
  - Duration units: `y` (year), `M` (month), `w` (week), `d` (day), `h` (hour), `m` (minute), `s` (second)

### Functions

**Global functions:**
- `date(string)` - Parse date string
- `now()` - Current date/time
- `today()` - Today at midnight
- `if(condition, trueValue, falseValue)` - Conditional logic
- `link(path, display)` - Create wikilink
- `file(path)` - Reference file object
- `list(element)` - Create list

**File functions:**
- `file.hasTag("tag1", "tag2")` - Check if file has tags
- `file.hasLink(otherFile)` - Check if file links to another
- `file.hasProperty("name")` - Check if property exists
- `file.inFolder("folder")` - Check if file in folder

**String functions:**
- `string.contains(value)` - Check substring
- `string.startsWith(query)` - Check prefix
- `string.endsWith(query)` - Check suffix
- `string.replace(pattern, replacement)` - Replace text
- `string.split(separator)` - Split into list
- `string.lower()` - Lowercase
- `string.trim()` - Remove whitespace

**List functions:**
- `list.contains(value)` - Check if list contains value
- `list.filter(condition)` - Filter list items
- `list.map(expression)` - Transform list items
- `list.sort()` - Sort list
- `list.unique()` - Remove duplicates
- `list.join(separator)` - Join into string

**Date functions:**
- `date.format("YYYY-MM-DD")` - Format date
- `date.relative()` - Relative time string
- `date.date()` - Date portion only
- `date.year`, `date.month`, `date.day` - Date components

**Number functions:**
- `number.round(digits)` - Round to digits
- `number.toFixed(precision)` - Fixed decimal places

### Formulas

Computed properties accessed as `formula.formulaname`:

```yaml
formulas:
  age_days: "(now() - file.ctime) / 86400000"
  display_name: 'if(alias, alias, file.name)'
  price_per_unit: "(price / quantity).round(2)"
  author_display: 'media/author.asLink()'
```

Formulas can reference:
- File properties (`file.name`, `file.mtime`, etc.)
- Note properties from frontmatter
- Other formulas
- Functions (global, string, list, date, number)

### Views

Configure how data is displayed:

```yaml
views:
  - type: table
    name: Table view
    limit: 50
    filters:
      and:
        - 'status == "active"'
    order:
      - file.mtime desc
      - file.name
    columns:
      - file.name
      - status
      - formula.age_days
  - type: cards
    name: Card view
    imageProperty: cover
    imageFit: cover
    imageAspectRatio: 1:1
```

**View types:**
- `table` - Tabular data with customizable row height
- `cards` - Card layout with optional image properties

**View properties:**
- `name` - View name (required)
- `limit` - Maximum number of results
- `filters` - View-specific filters (combine with global filters using AND logic)
- `order` - Sort order (property name + `asc`/`desc`)
- `columns` - Which properties/formulas to display (table only)
- `imageProperty`, `imageFit`, `imageAspectRatio` - Image settings (cards only)

### Special features

- **Current file context**: `this.file` - Reference current file (e.g., `file.hasLink(this.file)`)
- **Embedding**: `![[filename.base]]` or `![[filename.base#View Name]]`
- **Inline queries**: Use ` ```base ` code blocks in notes

## Execution steps

1. **Research vault properties**
   - Grep for property names in vault frontmatter
   - Identify property types (text, list, number, date, etc.)
   - Note common patterns and naming conventions
   - Find relevant tags if filtering by tags

2. **Research vault tags**
   - Find existing tag taxonomy
   - Identify relevant tags for the query
   - Ensure tag names are accurate

3. **Parse user request**
   - What data to query (files with certain tags/properties)
   - What to display (which properties/formulas)
   - How to filter (conditions)
   - How to sort (order)
   - View type (table or cards)

4. **Generate query**
   - Create filters section matching criteria
   - Add formulas if computed properties needed
   - Configure views with appropriate columns/settings
   - Ensure property names match vault schema exactly

5. **Validate**
   - Check YAML syntax is valid
   - Verify property names exist in vault
   - Confirm tag names are correct
   - Test filter logic is sound

6. **Output**
   - If `--file` specified: write to `.base` file in vault
   - Otherwise: return as ` ```base ` code block for inline use
   - Include explanation of what the query does

## Example queries

**Note:** These examples are syntax references from Obsidian Bases documentation.
They demonstrate query structure but may not reflect your vault's actual properties or tags.
Always research the vault first to find real property and tag names.

### Books rated above 4 stars

```base
filters:
  and:
    - file.hasTag("book")
    - media/rating > 4
formulas:
  author_display: 'media/author.asLink()'
  days_since_read: '(now() - media["publication date"]) / 86400000'
views:
  - type: table
    name: Highly rated books
    order:
      - media/rating desc
      - file.name
    columns:
      - file.name
      - formula.author_display
      - media/rating
```

### Active projects modified recently

```base
filters:
  and:
    - file.hasTag("project")
    - 'status == "active"'
    - file.mtime > now() - "1 week"
formulas:
  days_active: '(now() - file.ctime) / 86400000'
views:
  - type: table
    name: Recent active projects
    order:
      - file.mtime desc
    columns:
      - file.name
      - status
      - file.mtime
      - formula.days_active
```

### People I've talked to recently

```base
filters:
  and:
    - file.hasTag("identity")
    - file.hasProperty("last-contact")
    - last-contact > now() - "30d"
formulas:
  days_since_contact: '(now() - last-contact) / 86400000'
views:
  - type: cards
    name: Recent contacts
    order:
      - last-contact desc
  - type: table
    name: Contact list
    order:
      - last-contact desc
    columns:
      - file.name
      - last-contact
      - formula.days_since_contact
```

## Important notes

- **Research first** - Always grep vault to find exact property/tag names
- **Property name format** - Use forward slash notation: `media/author`, not `media.author`
- **Quote property names** - In expressions, quote properties with special chars: `media["publication date"]`
- **Type consistency** - Ensure operators match property types (numbers vs. strings vs. dates)
- **Date arithmetic** - Use string duration format: `"1d"`, `"2 weeks"`, `"3M"`
- **Formula references** - Access formulas with `formula.` prefix: `formula.age_days`
- **View filters** - Combine with global filters using AND logic
- **Be decisive** - Generate complete, working queries autonomously
