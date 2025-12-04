# Claude Code Configuration for OpenProject MCP Server

This directory contains Claude Code configuration files to optimize development workflow.

## 📁 Structure

```
.claude/
├── agents/           # Custom subagents
│   ├── mcp-reviewer.md      # Code review specialist
│   ├── api-explorer.md      # Fast codebase navigation
│   └── test-generator.md    # Pytest test generation
├── commands/         # Slash commands
│   ├── review-tool.md       # /review-tool - Review tool implementation
│   ├── add-tool.md          # /add-tool - Add new MCP tool
│   ├── test-coverage.md     # /test-coverage - Coverage analysis
│   ├── api-docs.md          # /api-docs - API documentation lookup
│   └── optimize-code.md     # /optimize-code - Performance optimization
├── hooks.json       # Automated workflow hooks
└── README.md        # This file
```

## 🤖 Custom Subagents

### mcp-reviewer (Sonnet)
Expert code reviewer for MCP tool implementations.

**Usage:**
```
@mcp-reviewer Please review the create_work_package tool implementation
```

**Best for:**
- Pre-merge code reviews
- Checking tool definitions match implementations
- Validating error handling patterns
- Security reviews

### api-explorer (Haiku - Fast!)
Quickly navigate codebase to find patterns and implementations.

**Usage:**
```
@api-explorer Find all tools that handle pagination
@api-explorer Where is authentication implemented?
```

**Best for:**
- Quick searches (3x faster than Sonnet)
- Finding code patterns
- Locating specific implementations
- Understanding codebase structure

### test-generator (Sonnet)
Generate comprehensive pytest tests with proper mocking.

**Usage:**
```
@test-generator Create tests for the list_work_packages tool
```

**Best for:**
- Writing new test files
- Increasing coverage
- Testing error scenarios
- Async/await test patterns

## ⚡ Slash Commands

### /review-tool <tool_name>
Review specific MCP tool implementation.

**Example:**
```
/review-tool create_work_package
```

### /add-tool <endpoint_name>
Scaffold new MCP tool with proper patterns.

**Example:**
```
/add-tool custom_fields
```

### /test-coverage [module]
Analyze test coverage and suggest improvements.

**Example:**
```
/test-coverage
/test-coverage src/tools/sprint_analytics.py
```

### /api-docs <endpoint>
Look up OpenProject API documentation.

**Example:**
```
/api-docs work_packages
/api-docs time_entries
```

### /optimize-code <file_or_function>
Analyze and optimize performance bottlenecks.

**Example:**
```
/optimize-code openproject-mcp.py
/optimize-code list_work_packages
```

## 🪝 Automated Hooks

### Pre-Tool-Use Hooks

1. **format-python-before-edit**
   - Auto-runs Black formatter before editing Python files
   - Non-blocking (doesn't prevent edits if formatting fails)

2. **protect-env-file**
   - **BLOCKS** attempts to edit `.env` file
   - Prevents accidental credential exposure

3. **validate-python-syntax**
   - Checks syntax before writing Python files
   - Non-blocking warning if validation unavailable

### Post-Tool-Use Hooks

1. **run-tests-after-tool-changes**
   - Automatically runs pytest after modifying tool files
   - Non-blocking (shows warning if tests not configured)

2. **update-requirements**
   - Syncs dependencies after `pyproject.toml` changes
   - Runs `uv sync` automatically

## 🎯 Model Selection Strategy

### Default: Sonnet 4.5
Use for most development tasks:
- Bug fixes and features
- Code reviews
- Writing tests
- Documentation

### Use Haiku 4.5 when:
- Quick searches (api-explorer agent)
- Rapid iteration (10+ calls/session)
- Simple refactoring
- Cost optimization needed
- **Benefit**: 3x cheaper, 2x faster

### Use Opus 4.5 when:
- Complex architectural decisions
- Large-scale refactoring
- Final review before merge
- Deep reasoning required
- **When**: Before production deploys

### Switch Models
```bash
# During session
/model haiku    # Switch to fast mode
/model opus     # Switch to deep thinking
/model sonnet   # Back to default

# At startup
claude --model haiku
```

## 🚀 Quick Start

### 1. Verify Setup
After checkout, Claude Code should auto-discover these configs.

### 2. Test Slash Commands
```
/api-docs work_packages
```

### 3. Try a Subagent
```
@api-explorer Find all error handling patterns
```

### 4. Check Hooks
Edit a Python file - Black formatter should run automatically.

## 💡 Best Practices

### When to Use Subagents
1. **Complex tasks** - Use general-purpose or specialized agents early
2. **Exploration** - Use api-explorer (Haiku) for fast searches
3. **Reviews** - Use mcp-reviewer before merging
4. **Testing** - Use test-generator to increase coverage

### Parallel Agent Execution
```
@api-explorer Find authentication flow
@test-generator Create tests for auth methods
```
Spawns 2 agents simultaneously for faster completion.

### Hook Customization
Edit `.claude/hooks.json` to:
- Add custom validation
- Integrate with CI tools
- Auto-format on save
- Run linters

### Command Arguments
Most commands support `$ARGUMENTS`:
```
/review-tool create_work_package
            ^^^^^^^^^^^^^^^^^^^
            This becomes $ARGUMENTS
```

## 🔧 Troubleshooting

### Hooks Not Running
1. Check `.claude/hooks.json` syntax (valid JSON)
2. Ensure commands are shell-compatible
3. Check timeout settings (default: 30s)

### Subagents Not Found
1. Verify `.claude/agents/*.md` files exist
2. Check YAML frontmatter syntax
3. Restart Claude Code if needed

### Slash Commands Not Appearing
1. Ensure files are in `.claude/commands/`
2. Check Markdown formatting
3. Look for `$ARGUMENTS` placeholder if needed

## 📚 Resources

- [Claude Code Docs](https://code.claude.com/docs)
- [Subagents Guide](https://code.claude.com/docs/en/sub-agents)
- [Hooks Documentation](https://code.claude.com/docs/en/hooks-guide)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

## 🤝 Contributing

When adding new agents/commands:
1. Follow existing naming conventions
2. Add clear descriptions in YAML frontmatter
3. Include usage examples in comments
4. Test before committing
5. Update this README

---

**Pro Tip**: Start with Sonnet for everything. If you find yourself running the same type of query 10+ times, switch to Haiku for that subtask. Save Opus for final reviews and complex decisions.
