# Hướng dẫn kết nối OpenProject MCP Server (Cloud)

Tài liệu này hướng dẫn người dùng nội bộ cách kết nối với OpenProject MCP Server đã được deploy lên FastMCP Cloud.

## Yêu cầu

1. **Claude Desktop**: Đã cài đặt Claude Desktop (phiên bản mới nhất)
2. **Connection URL**: Nhận từ admin (ví dụ: `https://your-org.fastmcp.cloud/openproject-mcp`)
3. **API Key** (tùy chọn): Nếu admin cấp API key riêng cho bạn

## Bước 1: Mở file cấu hình Claude Desktop

### Windows

1. Nhấn `Windows + R`
2. Gõ: `%APPDATA%\Claude`
3. Nhấn Enter
4. Mở file `claude_desktop_config.json` bằng Notepad hoặc editor bất kỳ

### macOS

1. Mở Terminal
2. Gõ: `open ~/Library/Application\ Support/Claude/`
3. Nhấn Enter
4. Mở file `claude_desktop_config.json` bằng TextEdit

### Linux

```bash
nano ~/.config/Claude/claude_desktop_config.json
```

## Bước 2: Thêm cấu hình MCP Server

### Cách 1: Kết nối chung (không có API key cá nhân)

Thêm đoạn code sau vào file `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openproject": {
      "url": "https://your-org.fastmcp.cloud/openproject-mcp",
      "transport": "sse"
    }
  }
}
```

**Lưu ý**: Thay `https://your-org.fastmcp.cloud/openproject-mcp` bằng URL thật mà admin cung cấp.

### Cách 2: Kết nối với API key cá nhân (được admin cấp)

```json
{
  "mcpServers": {
    "openproject": {
      "url": "https://your-org.fastmcp.cloud/openproject-mcp?key=YOUR_API_KEY_HERE",
      "transport": "sse"
    }
  }
}
```

**Lưu ý**: Thay `YOUR_API_KEY_HERE` bằng API key mà admin cấp cho bạn.

### Nếu đã có MCP servers khác

Nếu file `claude_desktop_config.json` đã có các MCP server khác, thêm `openproject` vào danh sách:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "openproject": {
      "url": "https://your-org.fastmcp.cloud/openproject-mcp",
      "transport": "sse"
    }
  }
}
```

## Bước 3: Lưu file và restart Claude Desktop

1. **Lưu file** `claude_desktop_config.json` (Ctrl+S / Cmd+S)
2. **Đóng hoàn toàn** Claude Desktop:
   - Windows: Right-click icon trong system tray → Quit
   - macOS: Cmd+Q
3. **Mở lại** Claude Desktop

## Bước 4: Kiểm tra kết nối

### 4.1. Kiểm tra MCP server có được load không

1. Mở Claude Desktop
2. Nhìn vào góc dưới bên trái, bạn sẽ thấy icon MCP (🔌 hoặc 🔧)
3. Click vào icon đó để xem danh sách MCP servers
4. Kiểm tra xem "openproject" có trong danh sách không

### 4.2. Test connection

Trong Claude Desktop, gõ:

```
Bạn có thể test kết nối đến OpenProject không?
```

Hoặc tiếng Anh:

```
Can you test the connection to OpenProject?
```

Claude sẽ sử dụng tool `test_connection` và trả về kết quả. Nếu thành công, bạn sẽ thấy:

```
✅ Connection successful!
Server: https://your-openproject.com
Version: 13.x.x
API Status: OK
```

## Bước 5: Bắt đầu sử dụng

Bây giờ bạn có thể yêu cầu Claude thực hiện các tác vụ với OpenProject:

### Ví dụ tiếng Việt:

```
Liệt kê tất cả các dự án đang active trong OpenProject
```

```
Tạo một task mới trong dự án "Website Redesign" với tiêu đề "Fix login bug" và priority là High
```

```
Hiển thị tất cả work packages được giao cho tôi
```

```
Cập nhật work package #123 thành status "In Progress"
```

### Ví dụ tiếng Anh:

```
List all active projects in OpenProject
```

```
Create a new task in project "Website Redesign" with subject "Fix login bug" and high priority
```

```
Show all work packages assigned to me
```

```
Update work package #123 to status "In Progress"
```

## Danh sách chức năng có sẵn

OpenProject MCP Server cung cấp 40 tools (công cụ) để làm việc với OpenProject:

### 1. Projects (Dự án)
- Liệt kê các dự án
- Xem chi tiết dự án
- Tạo/cập nhật/xóa dự án

### 2. Work Packages (Công việc)
- Liệt kê work packages
- Tạo/cập nhật/xóa work packages
- Xem types, statuses, priorities

### 3. Users & Memberships (Người dùng & Thành viên)
- Liệt kê users
- Quản lý project members
- Quản lý roles và permissions

### 4. Time Tracking (Theo dõi thời gian)
- Log time entries
- Xem time entries
- Quản lý activities

### 5. Work Package Relations (Quan hệ công việc)
- Tạo relations giữa work packages
- Quản lý parent-child hierarchy
- Liệt kê related work packages

### 6. Versions (Phiên bản)
- Tạo versions/milestones
- Liệt kê versions

## Troubleshooting (Xử lý lỗi)

### Lỗi: "MCP server openproject not found"

**Nguyên nhân**: Claude Desktop chưa load được cấu hình

**Giải pháp**:
1. Kiểm tra file `claude_desktop_config.json` có đúng format JSON không
2. Kiểm tra đường dẫn URL có đúng không
3. Restart lại Claude Desktop HOÀN TOÀN (phải quit, không chỉ close window)

### Lỗi: "Connection failed" hoặc "Server unavailable"

**Nguyên nhân**: Không kết nối được đến FastMCP Cloud server

**Giải pháp**:
1. Kiểm tra internet connection
2. Kiểm tra URL có đúng không (copy lại từ admin)
3. Nếu có firewall/proxy công ty, liên hệ IT support để whitelist domain `*.fastmcp.cloud`
4. Liên hệ admin để kiểm tra server có đang chạy không

### Lỗi: "Unauthorized" hoặc "Invalid API key"

**Nguyên nhân**: API key không đúng hoặc đã expire

**Giải pháp**:
1. Kiểm tra API key có copy đúng không (không có space thừa)
2. Liên hệ admin để lấy API key mới
3. Nếu không dùng API key cá nhân, xóa phần `?key=...` trong URL

### Lỗi: "Tool execution failed" khi chạy commands

**Nguyên nhân**: Có thể do permissions hoặc data không hợp lệ

**Giải pháp**:
1. Kiểm tra bạn có quyền thực hiện hành động đó trong OpenProject không
2. Kiểm tra data input có đúng format không (ví dụ: project ID phải là số)
3. Liên hệ admin để kiểm tra logs

### Claude không suggest tools OpenProject

**Nguyên nhân**: MCP server chưa được load đúng cách

**Giải pháp**:
1. Kiểm tra icon MCP có hiển thị ở góc dưới trái không
2. Click vào icon MCP, kiểm tra "openproject" có trong danh sách không
3. Thử gọi tool trực tiếp: "Use the test_connection tool to check OpenProject"

## Best Practices (Khuyến nghị)

### 1. Bảo mật API key
- Không share API key cá nhân của bạn với người khác
- Không commit file `claude_desktop_config.json` lên git
- Nếu API key bị lộ, liên hệ admin để revoke và lấy key mới

### 2. Sử dụng hiệu quả
- Hỏi rõ ràng và cụ thể để Claude hiểu đúng ý định
- Sử dụng project ID hoặc work package ID khi có thể (nhanh hơn search bằng tên)
- Kiểm tra kết quả trước khi thực hiện các hành động quan trọng (như xóa)

### 3. Performance
- Nếu queries chậm, thử chia nhỏ request (ví dụ: không list tất cả work packages, chỉ list theo project)
- Tránh spam nhiều requests liên tục trong thời gian ngắn

## Liên hệ support

Nếu gặp vấn đề không giải quyết được:

- **Slack**: #openproject-mcp-support
- **Email**: support@your-org.com
- **Admin**: Tên admin - admin@your-org.com

## FAQ (Câu hỏi thường gặp)

### Q: Tôi có cần cài đặt Python không?
**A**: Không. Khi dùng FastMCP Cloud, server đã chạy trên cloud rồi, bạn chỉ cần cấu hình Claude Desktop.

### Q: Tôi có thể dùng từ nhà và văn phòng không?
**A**: Có. Miễn là có internet, bạn có thể kết nối từ bất kỳ đâu. Cấu hình sẽ sync qua Claude account.

### Q: API key có expire không?
**A**: Tùy policy của công ty. Admin sẽ thông báo nếu cần renew.

### Q: Tôi có thể xem code của MCP server không?
**A**: Có. Code được open source tại: https://github.com/your-org/openproject-mcp-server

### Q: Dữ liệu của tôi có được log không?
**A**: Server chỉ log requests metadata (timestamp, tool name, user). Không log sensitive data như API keys hoặc nội dung work packages. Xem Privacy Policy để biết thêm chi tiết.

### Q: Tôi muốn contribute hoặc request feature mới?
**A**: Tuyệt vời! Tạo issue tại GitHub repo hoặc liên hệ team qua Slack.

---

**Phiên bản tài liệu**: 1.0
**Cập nhật lần cuối**: 2025-01-XX
**Ngôn ngữ**: Tiếng Việt
