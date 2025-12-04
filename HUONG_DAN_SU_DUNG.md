# Hướng Dẫn Sử Dụng OpenProject MCP - Tiếng Việt

**Dành cho**: 12 thành viên team Promete
**Phiên bản**: 2.0 (FastMCP)
**Ngày cập nhật**: 2 tháng 12, 2025

---

## 📖 Mục Lục

1. [Giới Thiệu](#giới-thiệu)
2. [Cài Đặt](#cài-đặt)
3. [Cách Sử Dụng](#cách-sử-dụng)
4. [Ví Dụ Thực Tế](#ví-dụ-thực-tế)
5. [Câu Hỏi Thường Gặp](#câu-hỏi-thường-gặp)
6. [Xử Lý Lỗi](#xử-lý-lỗi)

---

## 🎯 Giới Thiệu

OpenProject MCP cho phép bạn quản lý công việc trên OpenProject (manage.promete.ai) bằng ngôn ngữ tự nhiên qua Claude Code.

### Bạn có thể làm gì?

✅ Xem danh sách task của dự án
✅ Tạo task mới
✅ Cập nhật tiến độ task
✅ Giao task cho thành viên
✅ Theo dõi thời gian làm việc
✅ Quản lý thành viên dự án

**Tất cả bằng tiếng Việt!**

---

## 🔧 Cài Đặt

### Bước 1: Cài Claude Code

**Windows**:
1. Tải Claude Code từ: https://claude.ai/download
2. Cài đặt và mở ứng dụng

**macOS/Linux**:
```bash
# Xem hướng dẫn tại https://claude.ai/download
```

### Bước 2: Lấy OpenProject API Key

1. Đăng nhập vào https://manage.promete.ai
2. Click vào tên user (góc phải trên)
3. Chọn **"Tài khoản của tôi"**
4. Chọn tab **"Access tokens"**
5. Click **"+ API"** để tạo token mới
6. Copy token (ví dụ: `21c43c23c00356cbfb2695...`)

### Bước 3: Clone Repository

```bash
cd D:\Promete\Project  # Hoặc thư mục bất kỳ
git clone https://github.com/your-org/openproject-mcp-server.git
cd openproject-mcp-server
```

### Bước 4: Tạo File `.env`

Tạo file `.env` trong thư mục `openproject-mcp-server`:

```env
# OpenProject Configuration
OPENPROJECT_URL=https://manage.promete.ai
OPENPROJECT_API_KEY=paste_api_key_của_bạn_vào_đây

# Optional settings
LOG_LEVEL=INFO
```

**⚠️ LUU Ý**: Thay `paste_api_key_của_bạn_vào_đây` bằng API key bạn vừa copy ở Bước 2.

### Bước 5: Cài Đặt Dependencies

```bash
# Cài UV (package manager)
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Cài dependencies
uv sync
```

### Bước 6: Thêm MCP Server vào Claude Code

**Cách 1: Dùng CLI (Khuyến nghị)**
```bash
claude mcp add --transport stdio openproject-fastmcp \
  -e "PYTHONPATH=D:\\Promete\\Project\\openproject-mcp-server" \
  -- "D:\\Promete\\Project\\openproject-mcp-server\\.venv\\Scripts\\python.exe" \
     "D:\\Promete\\Project\\openproject-mcp-server\\openproject-mcp-fastmcp.py"
```

**Cách 2: Thủ công**
1. Mở file config:
   - Windows: `C:\Users\<tên_user>\AppData\Roaming\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Thêm vào:
```json
{
  "mcpServers": {
    "openproject-fastmcp": {
      "command": "D:\\Promete\\Project\\openproject-mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["D:\\Promete\\Project\\openproject-mcp-server\\openproject-mcp-fastmcp.py"],
      "env": {
        "PYTHONPATH": "D:\\Promete\\Project\\openproject-mcp-server"
      }
    }
  }
}
```

**Lưu ý**: Thay đổi đường dẫn cho phù hợp với máy bạn.

### Bước 7: Restart Claude Code

1. Đóng hoàn toàn Claude Code (Alt+F4)
2. Mở lại Claude Code
3. Kiểm tra icon MCP (🔌) ở góc dưới bên phải

✅ **Hoàn tất!** Giờ bạn có thể dùng Claude Code để quản lý OpenProject.

---

## 💬 Cách Sử Dụng

### Nguyên Tắc Chung

Bạn chỉ cần **hỏi bằng tiếng Việt tự nhiên**, Claude sẽ hiểu và thực hiện.

### 42 Công Cụ Có Sẵn

#### 📋 Quản Lý Task (9 tools)
- Xem danh sách task
- Tạo task mới
- Cập nhật task
- Xóa task
- Giao task cho người
- Bỏ giao task
- Xem loại task
- Xem trạng thái
- Xem độ ưu tiên

#### 📁 Quản Lý Dự Án (5 tools)
- Xem danh sách dự án
- Tạo dự án mới
- Cập nhật dự án
- Xóa dự án
- Xem chi tiết dự án

#### 👥 Quản Lý Người Dùng (6 tools)
- Xem danh sách users
- Xem thông tin user
- Xem vai trò (roles)
- Xem thành viên dự án
- Xem dự án của user

#### 🔗 Quản Lý Mối Quan Hệ (5 tools)
- Tạo quan hệ task (phụ thuộc, chặn, liên quan)
- Xem quan hệ
- Cập nhật quan hệ
- Xóa quan hệ

#### ⏱️ Theo Dõi Thời Gian (5 tools)
- Xem time log
- Tạo time entry
- Cập nhật time entry
- Xóa time entry
- Xem loại hoạt động

#### 🌲 Phân Cấp Task (3 tools)
- Set task cha/con
- Xóa phân cấp
- Xem task con

#### 👥 Quản Lý Thành Viên (5 tools)
- Xem memberships
- Thêm thành viên vào dự án
- Cập nhật vai trò
- Xóa thành viên

#### 📌 Quản Lý Phiên Bản (2 tools)
- Xem versions
- Tạo version mới

#### 🔧 Tiện Ích (2 tools)
- Test kết nối
- Kiểm tra quyền

---

## 🎬 Ví Dụ Thực Tế

### 1. Xem Task Của Dự Án

**Bạn hỏi**:
```
Cho tôi xem tất cả task của dự án Fintech
```

**Claude trả lời**:
```
✅ Found 15 work packages:

- **Implement login API** (#123)
  Type: Task
  Status: In Progress
  Assignee: Nguyễn Văn A
  Due: 2025-01-15

- **Fix bug in payment** (#124)
  Type: Bug
  Status: New
  Priority: High
  ...
```

### 2. Tạo Task Mới

**Bạn hỏi**:
```
Tạo task mới trong dự án Fintech:
- Tiêu đề: "Thiết kế giao diện dashboard"
- Loại: Task
- Mô tả: "Thiết kế UI/UX cho trang dashboard admin"
- Deadline: 2025-01-20
```

**Claude trả lời**:
```
✅ Work package #125 created successfully!

Subject: Thiết kế giao diện dashboard
Type: Task
Status: New
Due Date: 2025-01-20
```

### 3. Giao Task Cho Người

**Bước 1: Xem danh sách users**
```
Cho tôi xem danh sách người dùng
```

**Bước 2: Giao task**
```
Giao task 125 cho người dùng số 7
```

**Claude trả lời**:
```
✅ Work package #125 assigned successfully!

Subject: Thiết kế giao diện dashboard
Assigned to: Trần Thị B
Type: Task
Status: New
```

### 4. Cập Nhật Tiến Độ

**Bạn hỏi**:
```
Cập nhật task 125 lên 50% hoàn thành và chuyển sang In Progress
```

**Claude trả lời**:
```
✅ Work package #125 updated successfully!

Subject: Thiết kế giao diện dashboard
Status: In Progress
Progress: 50%
```

### 5. Log Thời Gian Làm Việc

**Bạn hỏi**:
```
Tôi đã làm task 125 được 3 giờ hôm nay, hoạt động là Development
```

**Claude trả lời**:
```
✅ Time entry created successfully!

Hours: 3
Date: 2025-01-15
Work Package: Thiết kế giao diện dashboard
Activity: Development
```

### 6. Xem Task Được Giao Cho Mình

**Bạn hỏi**:
```
Cho tôi xem các task được giao cho user số 7
```

### 7. Tạo Task Phụ Thuộc

**Bạn hỏi**:
```
Task 126 phải làm sau khi task 125 xong
```

**Claude trả lời**:
```
✅ Relation created successfully!

Type: follows
From: Task #126
To: Task #125
```

### 8. Xem Các Loại Task Có Sẵn

**Bạn hỏi**:
```
Cho tôi xem các loại task có thể tạo
```

**Claude trả lời**:
```
✅ Available Work Package Types:

- **Task** (ID: 1)
  ✓ Default type

- **Bug** (ID: 2)

- **Feature** (ID: 3)

- **Epic** (ID: 4)
```

### 9. Xem Trạng Thái Task

**Bạn hỏi**:
```
Liệt kê tất cả trạng thái của task
```

### 10. Thêm Thành Viên Vào Dự Án

**Bạn hỏi**:
```
Thêm user 8 vào dự án Fintech với vai trò Developer
```

---

## ❓ Câu Hỏi Thường Gặp

### Q1: Làm sao biết ID của user/project/task?

**A**: Hỏi Claude trước:
```
Cho tôi xem danh sách người dùng
Cho tôi xem danh sách dự án
Cho tôi xem task của dự án X
```

### Q2: Tôi có thể dùng tiếng Anh không?

**A**: Có! Claude hiểu cả tiếng Việt và tiếng Anh.

### Q3: Task ID là gì?

**A**: Là số hiện trên OpenProject, ví dụ: #123, #456

### Q4: Làm sao xóa task?

**A**:
```
Xóa task số 123
```

**⚠️ Cảnh báo**: Không thể hoàn tác!

### Q5: Tôi có thể tạo nhiều task cùng lúc không?

**A**: Có, hỏi từng task một hoặc yêu cầu Claude tạo list:
```
Tạo 3 task sau trong dự án Fintech:
1. "Viết unit test cho API login"
2. "Review code module payment"
3. "Deploy lên staging server"
```

### Q6: Làm sao xem task đã đóng?

**A**:
```
Cho tôi xem tất cả task của dự án Fintech, bao gồm cả task đã đóng
```

### Q7: Time entry activity ID là gì?

**A**:
- 1: Management (Quản lý)
- 2: Specification (Phân tích)
- 3: Development (Phát triển)
- 4: Testing (Kiểm thử)

### Q8: Làm sao bỏ giao task?

**A**:
```
Bỏ giao task số 123
```

---

## 🔧 Xử Lý Lỗi

### Lỗi: "MCP server not showing up"

**Nguyên nhân**: Claude Code chưa thấy server

**Giải pháp**:
1. Kiểm tra file config JSON syntax đúng chưa
2. Kiểm tra đường dẫn (absolute path, dùng `\\` trên Windows)
3. Kiểm tra file `.env` có trong thư mục project
4. Restart Claude Code hoàn toàn

**Test thủ công**:
```bash
cd D:\Promete\Project\openproject-mcp-server
uv run python openproject-mcp-fastmcp.py
# Phải thấy: "Loading tool modules..." và "Tool modules loaded successfully"
```

### Lỗi: "Connection failed"

**Nguyên nhân**: Không connect được tới OpenProject

**Giải pháp**:
1. Kiểm tra file `.env`:
   ```env
   OPENPROJECT_URL=https://manage.promete.ai
   OPENPROJECT_API_KEY=your_key_here
   ```
2. Kiểm tra API key còn hợp lệ không (vào OpenProject → Access tokens)
3. Kiểm tra mạng có kết nối được tới manage.promete.ai không

**Test kết nối**:
```bash
curl https://manage.promete.ai/api/v3
```

### Lỗi: "Permission denied"

**Nguyên nhân**: API key không có quyền

**Giải pháp**:
1. Vào OpenProject kiểm tra quyền của user
2. Tạo API key mới với đủ quyền
3. Hỏi admin cấp quyền

### Lỗi: "Tool not working"

**Nguyên nhân**: Tool gặp lỗi khi thực thi

**Giải pháp**:
1. Xem logs trong Claude Code (View → Developer Tools → Console)
2. Test tool riêng lẻ:
   ```bash
   uv run python -c "from src.tools.connection import test_connection; import asyncio; print(asyncio.run(test_connection()))"
   ```

### Lỗi: "Unicode encoding error" (Windows)

**Nguyên nhân**: Lỗi cosmetic với emoji trên Windows

**Giải pháp**: Bỏ qua, không ảnh hưởng chức năng

---

## 📚 Tài Liệu Tham Khảo

- **OpenProject API**: https://www.openproject.org/docs/api/
- **FastMCP Docs**: https://gofastmcp.com
- **Claude Code**: https://claude.ai/code
- **Migration Summary**: [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)

---

## 🆘 Hỗ Trợ

**Gặp vấn đề?**
1. Đọc phần [Xử Lý Lỗi](#xử-lý-lỗi) trước
2. Hỏi trong Slack channel team
3. Liên hệ admin: haunt150603@gmail.com

---

## 📝 Changelog

**Version 2.0** (2025-01-02)
- ✅ Migrate lên FastMCP framework
- ✅ 42 tools hoàn chỉnh (tăng từ 40)
- ✅ Thêm assign/unassign tools
- ✅ Hỗ trợ tiếng Việt đầy đủ
- ✅ Giảm 82% code (dễ maintain)

**Version 1.0** (2024-12-01)
- Initial release với 40 tools

---

**Made with ❤️ by Promete Team**
