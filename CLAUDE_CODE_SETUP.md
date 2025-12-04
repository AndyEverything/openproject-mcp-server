# Claude Code Testing Guide - FastMCP OpenProject

## Quick Setup (5 phút)

### Bước 1: Backup Config Hiện Tại
```bash
cp "%APPDATA%\Claude\claude_desktop_config.json" "%APPDATA%\Claude\claude_desktop_config.json.backup"
```

### Bước 2: Add FastMCP Server vào Config

**Location**: `C:\Users\haunt\AppData\Roaming\Claude\claude_desktop_config.json`

**Thêm vào config**:
```json
{
  "mcpServers": {
    "openproject-fastmcp": {
      "command": "d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server"
      }
    }
  }
}
```

**Hoặc nếu đã có server khác**:
```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "openproject-fastmcp": {
      "command": "d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server\\openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "d:\\Promete\\Project\\mcp-openproject\\openproject-mcp-server"
      }
    }
  }
}
```

### Bước 3: Restart Claude Code
- Đóng hoàn toàn Claude Code
- Mở lại Claude Code
- Kiểm tra MCP icon (🔌) ở góc dưới bên phải

---

## Test Cases (7 tools)

### Test 1: Connection Test ✅
**Command**:
```
Test connection to OpenProject API
```

**Expected Output**:
```
✅ API connection successful!

Instance Version: 12.x.x
Core Version: 12.x.x
```

---

### Test 2: Check Permissions ✅
**Command**:
```
Check my OpenProject permissions
```

**Expected Output**:
```
✅ User Permissions Retrieved

Name: [Your Name]
Email: [Your Email]
Login: [Your Login]
Status: active
Admin: Yes/No
```

---

### Test 3: List Projects ✅
**Command**:
```
List all active OpenProject projects
```

**Expected Output**:
```
✅ Found X project(s):

- **Project Name** (ID: 1)
  Status: Active
  Description: ...
```

---

### Test 4: List Work Packages (CRITICAL) ⭐
**Command**:
```
Show me all work packages, limit to 5
```

**Expected Output**:
```
✅ Found X work package(s):

- **Task Title** (#123)
  Type: Bug
  Status: In Progress
  Priority: High
  Assignee: John Doe
  Start: 2025-01-01
  Due: 2025-01-15
```

---

### Test 5: Get Project Details ✅
**Command**:
```
Get details of OpenProject project 5
```

**Expected Output**:
```
✅ Project #5

Name: [Project Name]
Identifier: [project-slug]
Status: Active
Public: Yes/No

Description:
[Project description...]
```

---

### Test 6: Create Work Package (CRITICAL) ⭐
**Command**:
```
Create a new work package:
- Project: 5
- Subject: "Test FastMCP Integration"
- Type: 1 (Task)
- Description: "Testing the new FastMCP implementation"
- Due date: 2025-01-20
```

**Expected Output**:
```
✅ Work package #[NEW_ID] created successfully!

Subject: Test FastMCP Integration
Type: Task
Status: New
Priority: Normal
Due Date: 2025-01-20
```

---

### Test 7: Update Work Package (CRITICAL) ⭐
**Command**:
```
Update work package 123:
- Status: 5 (In Progress)
- Assignee: 7
- Progress: 50%
- Due date: 2025-01-25
```

**Expected Output**:
```
✅ Work package #123 updated successfully!

Subject: [Task Title]
Type: [Type]
Status: In Progress
Priority: [Priority]
Assignee: [User Name]
Due Date: 2025-01-25
Progress: 50%
```

---

## Troubleshooting

### Issue 1: MCP Server Not Showing Up
**Symptoms**: Không thấy 🔌 icon hoặc tools không available

**Solutions**:
1. Check config file syntax (valid JSON)
2. Check paths (absolute paths, double backslashes)
3. Check .env file exists with OPENPROJECT_URL and OPENPROJECT_API_KEY
4. Restart Claude Code completely

**Verify manually**:
```bash
cd d:\Promete\Project\mcp-openproject\openproject-mcp-server
uv run python openproject-mcp-fastmcp.py
# Should see: "Loading tool modules..." and "Tool modules loaded successfully"
```

---

### Issue 2: Connection Failed
**Symptoms**: "❌ Connection failed" error

**Solutions**:
1. Check `.env` file:
```env
OPENPROJECT_URL=https://manage.promete.ai
OPENPROJECT_API_KEY=your_actual_api_key_here
```

2. Test connection manually:
```bash
uv run python test_tools.py
```

3. Check OpenProject is accessible:
```bash
curl https://manage.promete.ai/api/v3
```

---

### Issue 3: Tools Not Working
**Symptoms**: Tools show up but give errors when called

**Solutions**:
1. Check logs in Claude Code (View → Developer Tools → Console)
2. Test individual tool:
```bash
cd d:\Promete\Project\mcp-openproject\openproject-mcp-server
uv run python -c "from src.tools.connection import test_connection; import asyncio; print(asyncio.run(test_connection()))"
```

---

## Advanced: Test HTTP Transport

If you want to test HTTP transport for 12 users:

### Start HTTP Server
```bash
cd d:\Promete\Project\mcp-openproject\openproject-mcp-server

# Set API keys
set MCP_API_KEYS=test-key:TestUser

# Start server
uv run python openproject-mcp-http.py
```

### Test with curl
```bash
# List tools
curl http://localhost:8000/mcp/tools

# Call tool
curl -H "Authorization: Bearer test-key" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:8000/mcp/tools/call \
     -d "{\"name\": \"test_connection\", \"arguments\": {}}"
```

---

## Success Indicators

✅ **All 7 tools working if**:
- [ ] test_connection shows version
- [ ] check_permissions shows user info
- [ ] list_projects shows your projects
- [ ] list_work_packages shows tasks
- [ ] get_project shows project details
- [ ] create_work_package creates new task (check in OpenProject)
- [ ] update_work_package updates existing task (check in OpenProject)

⚠️ **Common Issues**:
- Unicode errors (cosmetic, ignore)
- Timeout on first call (warming up, retry)
- Permission denied (check API key permissions)

---

## Next Steps After Testing

### If All Tests Pass ✅
- Continue to Phase 2 (migrate 33 remaining tools)
- Deploy to Docker for HTTP transport
- Generate API keys for 12 users

### If Issues Found ⚠️
- Report specific error messages
- Share Claude Code logs
- We'll debug and fix issues

---

## Quick Reference

**Config Location**: `%APPDATA%\Claude\claude_desktop_config.json`
**Server Entry Point**: `openproject-mcp-fastmcp.py`
**Test Script**: `test_tools.py`
**Environment**: `.env`
**Logs**: Claude Code → View → Developer Tools → Console

**Available Tools**:
1. test_connection
2. check_permissions
3. list_projects
4. get_project
5. list_work_packages (CRITICAL)
6. create_work_package (CRITICAL)
7. update_work_package (CRITICAL)
