# 🤖 Claude Code Setup Guide - OpenProject MCP Server

Complete guide for optimizing Claude Code with this project.

## 📋 Table of Contents
- [Quick Start](#-quick-start)
- [Subagents Overview](#-subagents-overview)
- [Slash Commands](#-slash-commands)
- [Model Selection](#-model-selection)
- [Automated Hooks](#-automated-hooks)
- [Common Workflows](#-common-workflows)
- [Best Practices](#-best-practices)

## 🚀 Quick Start

### 1. Verify Configuration
```bash
# Check .claude directory exists
ls -la .claude/

# Should see:
# - agents/        (3 custom subagents)
# - commands/      (5 slash commands)
# - hooks.json     (automated workflows)
# - config.json    (model settings)
# - README.md      (detailed docs)
```

### 2. Test Setup
```bash
# In Claude Code, try:
/api-docs work_packages

# Should display OpenProject API documentation
```

### 3. Use Your First Subagent
```
@api-explorer Find all tools that handle pagination
```

## 🤖 Subagents Overview

### Built-in Subagents (Always Available)

#### general-purpose
- **Purpose**: Complex, multi-step tasks requiring both exploration and modification
- **Can**: Read, write, search, run commands
- **When**: Default for most coding tasks
- **Model**: Inherits from parent (usually Sonnet)

#### Explore
- **Purpose**: Fast codebase navigation and search
- **Can**: Read, search (Glob, Grep)
- **Cannot**: Modify files
- **When**: "Where is X?", "Find all Y", "How does Z work?"
- **Model**: Inherits from parent
- **Thoroughness levels**:
  - `quick` - Fast, basic searches
  - `medium` - Balanced exploration
  - `very thorough` - Comprehensive analysis

#### Plan
- **Purpose**: Research during plan mode
- **Auto-triggered**: When in plan mode
- **When**: Designing complex features/refactors

### Custom Subagents (Project-Specific)

#### @mcp-reviewer (Sonnet)
**Expert MCP code reviewer**

```
# Usage examples:
@mcp-reviewer Review the create_work_package implementation
@mcp-reviewer Check if error handling follows project patterns
@mcp-reviewer Security review for authentication flow
```

**Reviews:**
- Tool definitions vs implementations
- Async/await patterns
- Error handling standards
- API integration quality
- Response formatting
- Security issues

**Output:** Critical issues, suggestions, security notes, good practices

#### @api-explorer (Haiku - 3x faster!)
**Fast codebase explorer**

```
# Usage examples:
@api-explorer Find all error handling patterns
@api-explorer Where is authentication implemented?
@api-explorer List all tools that use pagination
@api-explorer How does response formatting work?
```

**Best for:**
- Quick searches (uses Haiku model)
- Finding code patterns
- Locating implementations
- Understanding structure

**Speed:** 2x faster than Sonnet, 3x cheaper

#### @test-generator (Sonnet)
**Pytest test generator**

```
# Usage examples:
@test-generator Create tests for list_work_packages tool
@test-generator Generate error handling tests
@test-generator Add integration tests for authentication
```

**Generates:**
- Async pytest tests
- Mock patterns for aiohttp
- Error scenario tests
- Input validation tests
- Coverage improvements

## ⚡ Slash Commands

### /review-tool <tool_name>
Review specific MCP tool implementation.

```bash
# Examples:
/review-tool create_work_package
/review-tool list_time_entries
/review-tool assign_work_package
```

**Checks:**
- Tool definition consistency
- Error handling
- Response formatting
- API integration
- Security

### /add-tool <endpoint_name>
Scaffold new MCP tool following project patterns.

```bash
# Examples:
/add-tool custom_fields
/add-tool notifications
/add-tool webhooks
```

**Workflow:**
1. Research OpenProject API endpoint
2. Add tool definition to `list_tools()`
3. Implement in `call_tool()`
4. Add client method if needed
5. Test the tool

### /test-coverage [module]
Analyze test coverage and generate missing tests.

```bash
# Examples:
/test-coverage                          # All code
/test-coverage openproject-mcp.py       # Main file
/test-coverage src/tools/               # Tools directory
```

**Output:**
- Coverage percentage
- Untested lines
- Priority recommendations
- Sample test code

### /api-docs <endpoint>
Look up OpenProject API v3 documentation.

```bash
# Examples:
/api-docs work_packages
/api-docs time_entries
/api-docs relations
/api-docs memberships
```

**Returns:**
- Endpoint details
- Request/response format
- Examples
- Permissions required
- Filter syntax

### /optimize-code <target>
Performance analysis and optimization suggestions.

```bash
# Examples:
/optimize-code openproject-mcp.py
/optimize-code list_work_packages
/optimize-code src/analytics/
```

**Analyzes:**
- Async/await patterns
- API call efficiency
- Memory usage
- Error handling overhead
- Response formatting

## 🎯 Model Selection

### Decision Tree

```
Is it architectural/complex design?
├─ YES → Use Opus 4.5
└─ NO → Is it a quick search/repetitive task?
    ├─ YES → Use Haiku 4.5 (3x cheaper, 2x faster)
    └─ NO → Use Sonnet 4.5 (default)
```

### Model Comparison

| Model | Speed | Cost | Use Cases |
|-------|-------|------|-----------|
| **Haiku 4.5** | 2x faster | 3x cheaper | Quick searches, rapid iteration, simple fixes, api-explorer agent |
| **Sonnet 4.5** | Balanced | Standard | Daily coding, reviews, tests, docs (DEFAULT) |
| **Opus 4.5** | Slower | Premium | Architecture, complex refactoring, final reviews |

### When to Use Each Model

#### Sonnet 4.5 (Default) ✅
```bash
# Daily driver for:
- Bug fixes
- Feature implementation
- Writing tests
- Code reviews
- Documentation
- Most refactoring

# 90% of your work should use Sonnet
```

#### Haiku 4.5 (Fast Mode) ⚡
```bash
# Switch to Haiku for:
- Quick file searches (10+ searches)
- Rapid prototyping
- Simple edits
- UI scaffolding
- Worker agents
- Cost optimization

# Command:
/model haiku

# In subagent:
@api-explorer (already uses Haiku)
```

**Performance:**
- 90% capability of Sonnet
- 2x faster execution
- 3x cost savings
- Ideal for >10 similar tasks

**Limitations:**
- Shorter context memory
- Less deep reasoning
- Not for complex architecture

#### Opus 4.5 (Deep Thinker) 🧠
```bash
# Use Opus for:
- Complex architectural decisions
- Large-scale refactoring (10+ files)
- Security reviews before deploy
- Final review before merge
- Extended reasoning tasks

# Command:
/model opus

# Hybrid approach:
/model opusplan  # Opus for planning, Sonnet for execution
```

**When NOT to use:**
- Simple bug fixes (overkill)
- Quick searches (expensive)
- Repetitive tasks (slow)

### Model Switching

```bash
# During session
/model haiku    # Switch to fast mode
/model sonnet   # Back to default
/model opus     # Deep thinking mode
/model opusplan # Hybrid: plan with Opus, execute with Sonnet

# At startup
claude --model haiku
claude --model sonnet
claude --model opus
```

### Cost Optimization Strategy

```
1. Start with Sonnet (default)
2. If doing 10+ similar searches → Switch to Haiku
3. Before production merge → Use Opus for final review
4. Back to Sonnet for next feature
```

**Example Session:**
```bash
# Feature development (Sonnet)
Implement user authentication

# Many searches needed (Haiku)
/model haiku
@api-explorer Find all API endpoints
@api-explorer Locate error handling patterns
... (10 more searches)

# Back to implementation (Sonnet)
/model sonnet
Implement the authentication logic

# Final review (Opus)
/model opus
@mcp-reviewer Security review before merge
```

## 🪝 Automated Hooks

### Pre-Tool-Use Hooks (Run BEFORE actions)

#### 1. format-python-before-edit
- **Trigger**: Before Edit/Write on `.py` files
- **Action**: Runs Black formatter
- **Blocking**: No (continues even if formatting fails)

#### 2. protect-env-file
- **Trigger**: Before Edit/Write on `.env` file
- **Action**: Shows error, prevents edit
- **Blocking**: YES (stops the edit)
- **Why**: Prevent credential exposure

#### 3. validate-python-syntax
- **Trigger**: Before Write on `.py` files
- **Action**: Checks syntax with `python -m py_compile`
- **Blocking**: No (warning only)

### Post-Tool-Use Hooks (Run AFTER actions)

#### 1. run-tests-after-tool-changes
- **Trigger**: After editing `openproject-mcp.py` or `src/tools/`
- **Action**: Runs `pytest tests/ -v`
- **Blocking**: No (shows results)
- **Why**: Catch breaking changes immediately

#### 2. update-requirements
- **Trigger**: After editing `pyproject.toml`
- **Action**: Runs `uv sync`
- **Blocking**: No
- **Why**: Keep dependencies in sync

### Hook Configuration

Edit [.claude/hooks.json](.claude/hooks.json) to customize:

```json
{
  "hooks": {
    "preToolUse": [
      {
        "name": "your-hook-name",
        "description": "What it does",
        "command": "shell command to run",
        "block": true  // or false
      }
    ]
  },
  "settings": {
    "timeout": 30000  // 30 seconds
  }
}
```

**Available Variables:**
- `$TOOL_NAME` - Name of tool being used (Edit, Write, Bash, etc.)
- `$TOOL_ARGUMENTS` - Arguments passed to the tool
- `$WORKSPACE_PATH` - Project root directory

## 🔄 Common Workflows

### Workflow 1: Adding New MCP Tool

```bash
# 1. Research API (Haiku for speed)
/model haiku
/api-docs custom_fields

# 2. Generate scaffold (Sonnet)
/model sonnet
/add-tool custom_fields

# 3. Implement (Claude does this)
# Auto-formatting hook runs on save

# 4. Generate tests (test-generator)
@test-generator Create tests for custom_fields tool

# 5. Review before commit (mcp-reviewer)
@mcp-reviewer Review custom_fields implementation

# 6. Final check (Opus)
/model opus
Review the entire custom_fields feature for production readiness
```

### Workflow 2: Bug Fix

```bash
# 1. Find bug location (Haiku for speed)
/model haiku
@api-explorer Find error handling in list_work_packages

# 2. Fix bug (Sonnet)
/model sonnet
Fix the error handling issue in list_work_packages

# Auto-hook: Tests run after edit
# Auto-hook: Black formatter runs

# 3. Verify fix
/test-coverage list_work_packages
```

### Workflow 3: Performance Optimization

```bash
# 1. Analyze bottlenecks
/optimize-code openproject-mcp.py

# 2. Implement optimizations (Sonnet)
Apply the recommended async/await optimizations

# 3. Verify improvements
Run performance benchmarks

# 4. Review (Opus before merge)
/model opus
@mcp-reviewer Final review of performance changes
```

### Workflow 4: Parallel Research

```bash
# Spawn multiple agents simultaneously
@api-explorer Find all pagination implementations
@api-explorer Locate authentication flow
@test-generator Create tests for auth methods

# All run in parallel, results aggregated
```

### Workflow 5: Large Refactoring

```bash
# 1. Plan with Opus
/model opusplan
Refactor work package tools to use shared validation

# Opus plans, then switches to Sonnet for execution

# 2. Test coverage check
/test-coverage src/tools/

# 3. Generate missing tests
@test-generator Create tests for shared validation

# 4. Final review with Opus
/model opus
@mcp-reviewer Security and quality review before merge
```

## 💡 Best Practices

### When to Use Subagents

✅ **DO use subagents for:**
- Complex problems (early in conversation)
- Parallel tasks (multiple agents simultaneously)
- Specialized reviews (mcp-reviewer)
- Fast searches (api-explorer with Haiku)
- Test generation (test-generator)

❌ **DON'T use subagents for:**
- Simple one-line fixes
- When you already have the file context
- Very straightforward tasks

### Subagent Efficiency Tips

1. **Use thoroughness levels wisely**
   ```
   @Explore[quick] Find the main function
   @Explore[medium] Understand error handling patterns
   @Explore[very thorough] Map entire authentication system
   ```

2. **Parallel execution for speed**
   ```
   # Run 3 agents at once:
   @api-explorer Find auth flow
   @api-explorer Find error patterns
   @test-generator Create auth tests
   ```

3. **Choose right model for agent**
   - Haiku for api-explorer (already configured)
   - Sonnet for mcp-reviewer and test-generator
   - Opus for critical reviews only

### Model Selection Best Practices

1. **Start with Sonnet** - Don't overthink it
2. **Switch to Haiku when repetitive** (10+ similar tasks)
3. **Save Opus for critical moments** (pre-merge, architecture)
4. **Use opusplan alias** for complex features
5. **Monitor costs** - Haiku is 3x cheaper

### Hook Best Practices

1. **Non-blocking by default** - Only block for critical issues
2. **Fast execution** - Keep hooks under 5 seconds
3. **Clear error messages** - Help users understand failures
4. **Idempotent** - Safe to run multiple times
5. **Team consistency** - Check hooks into git

### Slash Command Tips

1. **Use autocomplete** - Type `/` to see all commands
2. **Pass arguments** - Most commands accept `$ARGUMENTS`
3. **Chain commands** - Use multiple in sequence
4. **Create custom** - Add `.md` files to `.claude/commands/`
5. **Share with team** - Commands in git benefit everyone

## 🐛 Troubleshooting

### Issue: Subagents not found
```bash
# Check files exist
ls .claude/agents/

# Verify YAML frontmatter syntax
cat .claude/agents/mcp-reviewer.md

# Restart Claude Code
```

### Issue: Hooks not running
```bash
# Validate JSON syntax
cat .claude/hooks.json | python -m json.tool

# Check hook command syntax (should be shell-compatible)
# Windows: Use PowerShell syntax
# Linux/Mac: Use bash syntax
```

### Issue: Slash commands not appearing
```bash
# Check files in correct location
ls .claude/commands/

# Verify Markdown format
cat .claude/commands/review-tool.md

# Type `/` to see available commands
```

### Issue: Wrong model being used
```bash
# Check current model
/model

# Switch explicitly
/model sonnet

# Check config
cat .claude/config.json
```

## 📚 Additional Resources

### Official Documentation
- [Claude Code Docs](https://code.claude.com/docs)
- [Subagents Guide](https://code.claude.com/docs/en/sub-agents)
- [Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Community Resources
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code)
- [Claude Command Suite](https://github.com/qdhenry/Claude-Command-Suite)
- [VoltAgent Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)

### Guides & Tutorials
- [How I Use Every Claude Code Feature](https://blog.sshh.io/p/how-i-use-every-claude-code-feature)
- [Complete 2025 Developer's Guide](https://www.medianeth.dev/blog/claude-code-frameworks-subagents-2025)
- [Best Practices for Subagents](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)

## 🎓 Learning Path

### Week 1: Basics
1. Use built-in Explore agent for searches
2. Try 2-3 slash commands
3. Experiment with model switching

### Week 2: Intermediate
1. Use custom subagents (@mcp-reviewer, @api-explorer)
2. Create your first custom slash command
3. Optimize model usage (Haiku for repetitive tasks)

### Week 3: Advanced
1. Set up custom hooks
2. Parallel agent execution
3. Hybrid model strategies (opusplan)

### Week 4: Mastery
1. Create project-specific subagents
2. Custom workflow automation
3. Team configuration standards

---

## 🚀 Quick Reference Card

```bash
# Models
/model haiku     # Fast & cheap (3x savings, 2x speed)
/model sonnet    # Default (balanced)
/model opus      # Deep thinking (before merge)
/model opusplan  # Hybrid (plan with opus, execute with sonnet)

# Subagents
@mcp-reviewer     # Code review (Sonnet)
@api-explorer     # Fast search (Haiku)
@test-generator   # Test generation (Sonnet)

# Commands
/review-tool <name>      # Review implementation
/add-tool <endpoint>     # Scaffold new tool
/test-coverage [module]  # Coverage analysis
/api-docs <endpoint>     # API documentation
/optimize-code <target>  # Performance tips

# Workflows
Research → Haiku
Implement → Sonnet
Review → Opus
```

---

**Remember**: Start simple with Sonnet. Optimize later when patterns emerge. Most developers use Sonnet 90% of the time, Haiku for searches, and Opus for critical reviews.

Happy coding! 🎉
