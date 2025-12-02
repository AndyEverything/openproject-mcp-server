# OpenProject MCP Server - Deployment Guide

Tài liệu tổng quan về các tùy chọn deployment cho OpenProject MCP Server.

## Tổng quan

OpenProject MCP Server có thể được deploy theo 2 cách:

1. **Local (stdio)**: Chạy trên máy cá nhân, dùng cho 1 user
2. **Cloud (SSE)**: Deploy lên FastMCP Cloud, dùng cho team/organization

## So sánh các phương pháp Deployment

| Tiêu chí | Local (stdio) | Cloud (SSE) |
|----------|---------------|-------------|
| **Setup** | Phức tạp (cần Python, dependencies) | Đơn giản (chỉ cần URL) |
| **Users** | 1 người | Nhiều người |
| **Maintenance** | Mỗi user tự maintain | Centralized |
| **Updates** | Mỗi user tự update | Update 1 lần cho tất cả |
| **Access** | Chỉ khi local machine chạy | 24/7 từ bất kỳ đâu |
| **Cost** | Free (chạy local) | Có phí (tùy plan) |
| **Security** | API key trên local machine | API key centralized |
| **Performance** | Phụ thuộc local machine | Dedicated resources |
| **Monitoring** | Không có | Dashboard & alerts |

## Khi nào dùng Local (stdio)?

Dùng local deployment nếu:

- Chỉ có 1 người sử dụng
- Không muốn dùng cloud service
- Có yêu cầu security đặc biệt (không cho data ra ngoài)
- Đang trong giai đoạn development/testing
- Không có budget cho cloud hosting

**👉 Hướng dẫn**: Xem phần "Option 1: Local Deployment" trong [README.md](README.md)

## Khi nào dùng Cloud (SSE)?

Dùng cloud deployment nếu:

- Có nhiều users (team/organization)
- Muốn centralized management
- Cần 24/7 availability
- Muốn monitoring và alerts
- Không muốn user cài Python và dependencies
- Cần scale theo số lượng users

**👉 Hướng dẫn chi tiết**: Xem [FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md)

## Tài liệu liên quan

### Cho Admins (Deploy & Maintain)

1. **[FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md)** (English)
   - Hướng dẫn chi tiết cách deploy lên FastMCP Cloud
   - Cấu hình environment variables
   - Monitoring và troubleshooting
   - Security best practices

2. **[QUICK_START_CLOUD.md](QUICK_START_CLOUD.md)**
   - TL;DR version - các bước nhanh nhất
   - Common issues và solutions

3. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**
   - Checklist đầy đủ cho deployment
   - Pre-deployment, deployment, post-deployment
   - Monitoring và maintenance schedule

4. **[CLAUDE.md](CLAUDE.md)**
   - Technical documentation cho development
   - Architecture và code structure
   - Contributing guidelines

### Cho Users (Connect & Use)

1. **[HUONG_DAN_KET_NOI_CLOUD.md](HUONG_DAN_KET_NOI_CLOUD.md)** (Tiếng Việt)
   - Hướng dẫn kết nối với Cloud deployment
   - Troubleshooting cho users
   - Best practices

2. **[HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)** (Tiếng Việt)
   - Hướng dẫn sử dụng các tools
   - Ví dụ cụ thể bằng tiếng Việt

3. **[README.md](README.md)** (English)
   - Tổng quan về project
   - Local setup instructions
   - Tool documentation

## Quick Decision Tree

```
Bạn có nhiều hơn 1 user?
│
├─ Không → Dùng Local (stdio)
│         → Đọc README.md section "Option 1: Local Deployment"
│
└─ Có → Bạn có budget cho cloud hosting?
       │
       ├─ Không → Tự host với Docker
       │         → Đọc FASTMCP_CLOUD_DEPLOYMENT.md section "Alternative: Self-hosted"
       │
       └─ Có → Dùng FastMCP Cloud
                → Đọc FASTMCP_CLOUD_DEPLOYMENT.md
                → Follow DEPLOYMENT_CHECKLIST.md
                → Share HUONG_DAN_KET_NOI_CLOUD.md với users
```

## Architecture Diagrams

### Local (stdio) Architecture

```
┌─────────────────┐
│ Claude Desktop  │
│                 │
│ ┌─────────────┐ │
│ │ MCP Client  │ │
│ └──────┬──────┘ │
└────────┼────────┘
         │ stdio
         │
    ┌────▼────┐
    │  MCP    │
    │ Server  │ (Python process)
    └────┬────┘
         │ HTTP/API calls
         │
    ┌────▼─────────┐
    │  OpenProject │
    │   Instance   │
    └──────────────┘
```

### Cloud (SSE) Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ User 1 Claude   │     │ User 2 Claude   │     │ User 3 Claude   │
│    Desktop      │     │    Desktop      │     │    Desktop      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ SSE (HTTPS)          │ SSE (HTTPS)          │ SSE (HTTPS)
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                        ┌────────▼──────────┐
                        │  FastMCP Cloud    │
                        │                   │
                        │  ┌─────────────┐  │
                        │  │ MCP Server  │  │
                        │  │  (Python)   │  │
                        │  └──────┬──────┘  │
                        │         │         │
                        └─────────┼─────────┘
                                  │ HTTP/API calls
                                  │
                             ┌────▼─────────┐
                             │  OpenProject │
                             │   Instance   │
                             └──────────────┘
```

## Deployment Process Overview

### Local Deployment (stdio)

```bash
# 1. Clone & setup
git clone <repo>
cd openproject-mcp-server
uv sync

# 2. Configure
cp env_example.txt .env
# Edit .env with your credentials

# 3. Run
uv run python openproject-mcp-fastmcp.py

# 4. Configure Claude Desktop
# Edit claude_desktop_config.json
# Add stdio transport config

# 5. Done!
```

**Thời gian**: ~10 phút (cho mỗi user)

### Cloud Deployment (SSE)

```bash
# Admin side (one-time):
# 1. Deploy
uv sync
pip install fastmcp-cli
fastmcp login
fastmcp deploy

# 2. Configure on dashboard
# Set environment variables
# Get connection URL

# User side (repeat for each user):
# 3. Share URL với users
# Users edit claude_desktop_config.json
# Add SSE transport config with URL

# 4. Done!
```

**Thời gian**:
- Admin: ~30 phút (one-time)
- Per user: ~2 phút

## Migration Guide

### Từ Local sang Cloud

Nếu đang dùng local và muốn chuyển sang cloud:

1. **Admin**: Follow [FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md)
2. **Users**:
   - Backup current `claude_desktop_config.json`
   - Replace stdio config với SSE config
   - Test connection
   - Remove local MCP server (optional, có thể giữ làm backup)

### Từ Cloud về Local

Nếu muốn rollback từ cloud về local:

1. Follow "Option 1: Local Deployment" trong [README.md](README.md)
2. Replace SSE config với stdio config trong `claude_desktop_config.json`
3. Restart Claude Desktop

## Support & Resources

### Documentation

- **Technical**: [CLAUDE.md](CLAUDE.md)
- **Deployment**: [FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md)
- **User Guide**: [HUONG_DAN_SU_DUNG.md](HUONG_DAN_SU_DUNG.md)
- **Connection Guide**: [HUONG_DAN_KET_NOI_CLOUD.md](HUONG_DAN_KET_NOI_CLOUD.md)

### Getting Help

- **GitHub Issues**: https://github.com/your-org/openproject-mcp-server/issues
- **Internal Slack**: #openproject-mcp-support
- **Email**: support@your-org.com

### Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) section "Contributing Guidelines"

## Changelog

### v1.0.0 (2025-01-XX)
- Initial release
- 40 tools for OpenProject API v3
- Support for both stdio and SSE transports
- FastMCP Cloud deployment support
- Comprehensive documentation

---

**Maintained by**: Your Team
**Last Updated**: 2025-01-XX
**License**: MIT
