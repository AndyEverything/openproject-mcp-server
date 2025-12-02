# Hướng dẫn Deploy lên FastMCP Cloud

Tài liệu này hướng dẫn cách deploy OpenProject MCP Server lên FastMCP Cloud để người dùng nội bộ có thể truy cập từ bất kỳ đâu.

## Tổng quan

FastMCP Cloud là dịch vụ hosting MCP server, cho phép người dùng kết nối từ Claude Desktop mà không cần chạy server locally.

**Ưu điểm:**
- Không cần cài đặt Python hoặc dependencies trên máy user
- Tập trung quản lý API keys và cấu hình
- Truy cập từ bất kỳ đâu có internet
- Tự động scale và monitoring

## Yêu cầu

1. **Tài khoản FastMCP Cloud**: Đăng ký tại https://fastmcp.cloud
2. **OpenProject instance**: URL và API key
3. **Python 3.10+**: Để build và test local trước khi deploy

## Bước 1: Chuẩn bị code

### 1.1. Cài đặt dependencies mới

```bash
# Sync dependencies với SSE transport support
uv sync
```

### 1.2. Test local với SSE transport

```bash
# Chạy server với SSE transport
uv run python openproject-mcp-sse.py
```

Server sẽ chạy trên http://localhost:8000 (mặc định).

## Bước 2: Deploy lên FastMCP Cloud

FastMCP Cloud sử dụng **GitHub integration** - không cần CLI. Deployment được trigger tự động từ GitHub repo.

### 2.1. Push code lên GitHub

```bash
# Add và commit tất cả changes
git add .
git commit -m "Add FastMCP Cloud deployment support"

# Push lên GitHub
git push origin main
```

### 2.2. Tạo project trên FastMCP Cloud

1. Truy cập https://fastmcp.cloud
2. Click "Sign in with GitHub"
3. Authorize FastMCP Cloud để access repositories
4. Click "Create Project"
5. Chọn repository chứa code MCP server
   - Hoặc fork từ quickstart template nếu tạo mới

### 2.3. Configure project

Điền thông tin project:

**Basic Settings:**
- **Name**: `openproject-mcp` (hoặc tên bạn muốn)
  - Tên này sẽ tạo URL: `https://openproject-mcp.fastmcp.app/mcp`
- **Entry Point**: `openproject-mcp-sse.py`
  - File Python chứa FastMCP server với SSE transport
- **Authentication**: Enable
  - Chỉ members trong organization có thể dùng
  - Disable nếu muốn public access

**Environment Variables:**

Thêm các biến environment:
- `OPENPROJECT_URL` = `https://your-openproject.com`
- `OPENPROJECT_API_KEY` = `your-api-key-here`
- `OPENPROJECT_PROXY` = `http://proxy:3128` (optional)
- `LOG_LEVEL` = `INFO` (optional)

### 2.4. Deploy

1. Click "Deploy" button
2. FastMCP Cloud sẽ:
   - Clone repository từ GitHub
   - Detect dependencies từ `pyproject.toml`
   - Install dependencies
   - Build Docker container
   - Deploy container với SSE transport
3. Đợi 2-3 phút cho deployment hoàn tất
4. Status sẽ chuyển thành "Running" khi thành công

### 2.5. Lấy Connection URL

Sau khi deploy thành công, URL sẽ hiển thị trên dashboard:

```
https://your-project-name.fastmcp.app/mcp
```

Copy URL này để share với users.

## Bước 3: Kết nối từ Claude Desktop

### 3.1. Cấu hình Claude Desktop

Mở file cấu hình Claude Desktop:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Thêm cấu hình SSE:

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

**Lưu ý**: Thay `your-project-name` bằng tên project thật bạn đã tạo.

### 3.2. Restart Claude Desktop

Khởi động lại Claude Desktop để áp dụng cấu hình mới.

### 3.3. Kiểm tra kết nối

Trong Claude Desktop, gõ:
```
Can you test the connection to OpenProject?
```

Claude sẽ sử dụng tool `test_connection` để kiểm tra kết nối.

## Bước 4: Quản lý và Monitoring

### 4.1. Xem logs

Trên FastMCP Cloud dashboard:
1. Chọn project "openproject-mcp"
2. Click tab "Logs"
3. Xem realtime logs hoặc filter theo:
   - Level (ERROR, WARNING, INFO)
   - Time range
   - Search keywords

### 4.2. Monitoring Dashboard

Truy cập dashboard tại: https://fastmcp.cloud

Dashboard cung cấp:
- **Deployment Status**: Running, Stopped, Error
- **Request Metrics**: Total requests, requests/minute
- **Latency**: Average response time
- **Error Rates**: 4xx, 5xx errors
- **Resource Usage**: CPU, memory usage
- **Recent Logs**: Last 100 log entries

### 4.3. Update deployment

**Automatic Deployment từ GitHub:**

FastMCP Cloud tự động deploy khi có code changes:

```bash
# 1. Update code local
git pull origin main
# Make changes...

# 2. Commit và push
git add .
git commit -m "Update: description of changes"
git push origin main

# 3. FastMCP Cloud tự động detect và re-deploy
```

**Pull Request Deployments:**

FastMCP Cloud có CI/CD tự động:
- Mỗi PR tạo preview deployment riêng
- Test trên preview URL trước khi merge
- Merge vào main → auto-deploy lên production

### 4.4. Rollback nếu có lỗi

Trên dashboard:
1. Click tab "Deployments"
2. Xem list tất cả deployments (có git commit hash)
3. Click "Rollback" trên version trước đó
4. Confirm rollback

Hoặc rollback bằng cách:
- Revert git commit
- Push lên GitHub
- FastMCP Cloud tự động deploy version cũ

## Bước 5: Quản lý người dùng nội bộ

### 5.1. Phân quyền access

Trong FastMCP Cloud dashboard:

1. Vào "Team" > "Members"
2. Mời members qua email
3. Gán role:
   - **Admin**: Full access, có thể deploy và config
   - **Developer**: Có thể xem logs và metrics
   - **User**: Chỉ có thể sử dụng MCP server

### 5.2. Authentication

**Organization-level Authentication:**

Khi enable authentication trong project settings:
- Chỉ members trong FastMCP Cloud organization có thể access
- Users phải sign in với GitHub account đã được invite
- Không cần API key riêng cho mỗi user

**Public Access:**

Nếu disable authentication:
- Bất kỳ ai có URL đều có thể dùng
- Không recommend cho internal use
- Chỉ dùng cho demo hoặc public tools

**Per-User API Keys** (if supported by FastMCP Cloud):

Nếu cần track usage per user:
1. Admin tạo API keys riêng trên dashboard
2. Share URL với key cho từng user:
   ```
   https://your-project-name.fastmcp.app/mcp?key=user-specific-key
   ```
3. User config trong Claude Desktop:
   ```json
   {
     "mcpServers": {
       "openproject": {
         "url": "https://your-project-name.fastmcp.app/mcp?key=abc123...",
         "transport": "sse"
       }
     }
   }
   ```

## Security Best Practices

### 1. Không commit secrets

- File `.env` đã có trong `.gitignore`
- Chỉ config environment variables trên FastMCP Cloud dashboard
- Sử dụng `.env.example` làm template

### 2. Rotate API keys định kỳ

- Đổi OpenProject API key mỗi 3-6 tháng
- Update trên FastMCP Cloud dashboard
- Không cần thay đổi code

### 3. Giới hạn access

- Chỉ share FastMCP URL với người dùng nội bộ
- Sử dụng IP whitelist nếu FastMCP Cloud hỗ trợ
- Enable 2FA cho FastMCP Cloud account

### 4. Monitoring và Alerts

Cấu hình alerts trong dashboard:
- High error rate (>5% errors)
- High latency (>2s average)
- Resource usage >80%

## Troubleshooting

### Lỗi: "Connection refused"

**Nguyên nhân**: Server chưa start hoặc đang restart

**Giải pháp**:
- Check deployment status trên FastMCP Cloud dashboard
- Xem deployment logs để tìm errors
- Restart deployment từ dashboard nếu cần
- Verify URL đúng format: `https://project-name.fastmcp.app/mcp`

### Lỗi: "401 Unauthorized" từ OpenProject

**Nguyên nhân**: API key không đúng hoặc đã expire

**Giải pháp**:
1. Vào FastMCP Cloud dashboard > Project Settings
2. Tab "Environment Variables"
3. Update `OPENPROJECT_API_KEY` với key mới
4. Deployment sẽ tự động restart

### Lỗi: "Tool not found"

**Nguyên nhân**: Deployment thiếu files hoặc dependencies

**Giải pháp**:
- Kiểm tra `pyproject.toml` có đầy đủ dependencies không
- Verify entry point file `openproject-mcp-sse.py` tồn tại
- Check deployment logs để xem build errors
- Re-deploy từ dashboard
- Verify tất cả files trong `src/` được commit vào git

### Performance issues

**Nguyên nhân**: Resource không đủ hoặc quá nhiều concurrent requests

**Giải pháp**:
- Check resource usage trên dashboard
- Upgrade plan nếu cần more resources
- Optimize code để giảm memory usage
- Implement caching nếu có nhiều repeated requests
- Contact FastMCP support để increase limits

## Chi phí ước tính

Dựa trên pricing của FastMCP Cloud (giả định):

- **Free tier**: 100 requests/ngày, 256MB RAM
- **Starter**: $10/tháng - 10,000 requests/tháng, 512MB RAM
- **Team**: $50/tháng - 100,000 requests/tháng, 1GB RAM
- **Enterprise**: Custom pricing - Unlimited requests, custom resources

## Alternative: Self-hosted với Docker

Nếu không muốn dùng FastMCP Cloud, có thể tự host:

```bash
# Build Docker image
docker build -t openproject-mcp .

# Run với SSE transport
docker run -p 8000:8000 \
  -e OPENPROJECT_URL=https://... \
  -e OPENPROJECT_API_KEY=... \
  openproject-mcp python openproject-mcp-sse.py
```

Sau đó expose qua reverse proxy (nginx/caddy) với HTTPS.

## Support

- **GitHub Issues**: https://github.com/your-org/openproject-mcp-server/issues
- **Internal Slack**: #openproject-mcp-support
- **Email**: support@your-org.com

## Changelog

### v1.0.0 (2025-01-XX)
- Initial deployment to FastMCP Cloud
- 40 tools available
- SSE transport support
- Multi-user access control
