# Quick Start: Deploy to FastMCP Cloud

Tài liệu này cung cấp hướng dẫn nhanh để deploy OpenProject MCP Server lên FastMCP Cloud.

## TL;DR (Too Long; Didn't Read)

```bash
# 1. Update dependencies
uv sync

# 2. Push code to GitHub
git add .
git commit -m "Add FastMCP Cloud support"
git push origin main

# 3. Deploy on FastMCP Cloud (Web UI)
# Visit: https://fastmcp.cloud
# - Sign in with GitHub
# - Create project from your repo
# - Set entry point: openproject-mcp-sse.py
# - Configure environment variables
# - Click Deploy

# 4. Share URL with users
# URL format: https://your-project-name.fastmcp.app/mcp
# Users add to Claude Desktop config:
# {
#   "mcpServers": {
#     "openproject": {
#       "url": "https://your-project-name.fastmcp.app/mcp",
#       "transport": "sse"
#     }
#   }
# }
```

## Detailed Steps

### For Admins (One-time setup)

1. **Cài đặt dependencies cho SSE transport:**
   ```bash
   uv sync
   ```

2. **Test local trước khi deploy:**
   ```bash
   uv run python openproject-mcp-sse.py
   # Server chạy tại http://localhost:8000
   # Ctrl+C để stop
   ```

3. **Push code lên GitHub:**
   ```bash
   git add .
   git commit -m "Add FastMCP Cloud deployment support"
   git push origin main
   ```

4. **Deploy trên FastMCP Cloud:**
   - Truy cập: https://fastmcp.cloud
   - Click "Sign in with GitHub"
   - Authorize FastMCP Cloud
   - Click "Create Project"
   - Chọn repository của bạn (hoặc fork từ quickstart)
   - Điền thông tin:
     - **Name**: openproject-mcp (hoặc tên bạn muốn)
     - **Entry Point**: openproject-mcp-sse.py
     - **Authentication**: Enable (chỉ members trong org có thể dùng)

5. **Configure environment variables:**
   - Trong project settings, thêm Environment Variables:
     - `OPENPROJECT_URL` = https://your-openproject.com
     - `OPENPROJECT_API_KEY` = your-api-key-here
     - `OPENPROJECT_PROXY` = http://proxy:3128 (nếu có)
     - `LOG_LEVEL` = INFO
   - Click Save

6. **Deploy:**
   - Click "Deploy" button
   - Đợi build và deployment hoàn tất (~2-3 phút)
   - Status sẽ chuyển thành "Running"

7. **Lấy connection URL:**
   - URL sẽ hiển thị trên dashboard, dạng: `https://your-project-name.fastmcp.app/mcp`
   - Copy URL này để share với users

8. **Share với users:**
   - Gửi URL cho users qua email/Slack
   - Gửi kèm hướng dẫn: [HUONG_DAN_KET_NOI_CLOUD.md](HUONG_DAN_KET_NOI_CLOUD.md)

### For Users (Kết nối)

1. **Mở file cấu hình Claude Desktop:**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Thêm cấu hình:**
   ```json
   {
     "mcpServers": {
       "openproject": {
         "url": "https://your-project-name.fastmcp.app/mcp",
         "transport": "sse"
       }
     }
   }
   ```

   **Lưu ý**: Thay `your-project-name` bằng tên project thật từ admin

3. **Restart Claude Desktop**

4. **Test connection:**
   Gõ trong Claude: "Test connection to OpenProject"

## Common Issues

### ❌ "Connection failed"
- Kiểm tra server status trên FastMCP Cloud dashboard
- Xem deployment logs để tìm errors
- Restart deployment từ dashboard nếu cần

### ❌ "401 Unauthorized" từ OpenProject
- API key sai hoặc expire
- Update trên dashboard > Environment Variables

### ❌ "Tool execution failed"
- Check logs trên FastMCP Cloud dashboard
- Kiểm tra permissions trong OpenProject
- Verify environment variables được config đúng

## Next Steps

- 📖 Đọc full guide: [FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md)
- 🇻🇳 Hướng dẫn cho users: [HUONG_DAN_KET_NOI_CLOUD.md](HUONG_DAN_KET_NOI_CLOUD.md)
- 🐛 Report issues: GitHub Issues

## Support

- Slack: #openproject-mcp-support
- Email: support@your-org.com

---

**Version**: 1.0
**Last Updated**: 2025-01-XX
