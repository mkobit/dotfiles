# JSON Merge Rule Implementation Project
*Started: 2025-08-29*

## Project Overview
Implement a JSON merge type rule for targeted files, similar to the existing guarded install pattern. The system will:

1. Take input JSON file from source bazel dotfiles repository
2. Accept a JSON merge document (file or inline)
3. Optionally merge with existing home directory files
4. Install merged result deterministically
5. Support test generation and validation

## Goals
- **Phase 1**: Deterministic JSON merging in repo with known outputs
- **Phase 2**: Support merging with unmanaged home directory files
- **Phase 3**: Integration with existing guarded install system

## Key Requirements
- Use off-the-shelf tools (Python libraries preferred)
- Generate test rules for validation
- JSON schema validation support
- Deterministic output for build reproducibility

## Tasks
- [ ] Analyze current project structure and patterns
- [ ] Research JSON merge libraries
- [ ] Design rule architecture
- [ ] Implement core functionality
- [ ] Add test generation
- [ ] Integrate with guarded install
- [ ] Create validation framework

## Important Files
- `rules/common/guarded_install.bzl` - Existing guarded installation pattern
- `rules/validation.bzl` - JSON validation rules and patterns
- `tools/validation/json_schema_validation.bzl` - JSON schema validation framework
- `requirements.lock.txt` - Python dependencies (needs JSON merge libraries)

### Implemented Files
- `rules/json_merge/defs.bzl` - Public API for JSON merge rules
- `rules/json_merge/json_merge_tool.py` - Core Python merge implementation
- `rules/json_merge/private/json_merge.bzl` - Bazel rule implementation
- `rules/json_merge/BUILD.bazel` - Python binary and exports
- `test/json_merge/` - Comprehensive test suite with Claude hooks examples

## Research Findings

### JSON Merge Libraries (Completed)
1. **jsonmerge** - Schema-driven merging with complex strategies (Recommended)
2. **deepmerge** - Simple deep merging with strategy chains
3. **json-merge-patch** - RFC 7396 compliant, deterministic
4. **jq** - Command-line tool, widely available, powerful

### Recommended Approach
- **Primary**: jsonmerge for schema-driven deterministic merging
- **Secondary**: jq for final output normalization and determinism
- **Integration**: Hybrid approach combining Python logic with jq formatting

## Progress Log
- **2025-08-29**: Project started, initial planning
- **2025-08-29**: Analyzed existing project structure and patterns  
- **2025-08-29**: Completed research on JSON merge libraries and tools
- **2025-08-29**: Implemented core JSON merge rule with Python tool
- **2025-08-29**: Added Claude hooks specific merge strategy
- **2025-08-29**: Created comprehensive test suite - all tests passing
- **2025-08-29**: **MILESTONE**: Core functionality complete and validated

## Key Decisions
- Use jsonmerge as primary merge engine for schema flexibility
- Follow existing guarded_install pattern for file management
- Leverage existing validation.bzl patterns for test generation
- Add required dependencies to requirements.lock.txt
- **First use case**: Claude hooks JSON merging for independent hook files
- **No shell scripts**: Use Python rules for portability and avoid implicit dependencies

## Implementation Summary

### ✅ Completed Features
1. **Core JSON Merge Rule**: Python-based deterministic merging with configurable strategies
2. **Claude Hooks Strategy**: Specialized merge logic for independent Claude hooks files  
3. **Validation Framework**: Comprehensive JSON validation and Claude hooks schema validation
4. **Test Suite**: Unit tests and integration tests with Bazel - all passing
5. **Deterministic Output**: Sorted keys, consistent formatting, reproducible builds

### 🚀 Ready for Use
The JSON merge rule is now ready for production use with Claude hooks files:

```starlark
load("//rules/json_merge:defs.bzl", "json_merge")

json_merge(
    name = "merged_claude_hooks",
    srcs = [
        "base_hooks.json",
        "tool_specific_hooks.json",
        "project_hooks.json",
    ],
    out = "claude_hooks.json", 
    strategy = "claude_hooks",
    validate_claude_hooks = True,
)
```

### 📋 Next Steps (Future Work)
1. **Guarded Install Integration**: Complete the installation system for home directory deployment
2. **Advanced Merge Strategies**: Add support for jsonmerge library with schema-driven merging  
3. **jq Integration**: Add jq as secondary tool for advanced JSON transformations
4. **Dependencies**: Add jsonmerge to requirements.lock.txt when advanced strategies are needed

## Notes
- Focus on deterministic builds ✅
- Leverage existing Bazel patterns ✅  
- Prioritize testability and validation ✅
- Avoid shell scripts, use Python ✅