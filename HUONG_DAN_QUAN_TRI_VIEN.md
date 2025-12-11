# 📚 Hướng Dẫn Quản Trị Viên - OpenProject MCP Server

> **Dành cho:** Quản trị viên, Team Leader, Project Manager
> **Mục đích:** Quản lý công việc và tự động hóa quy trình làm việc bằng AI Claude Desktop

---

## 🎯 Tại Sao Nên Dùng?

Thay vì phải:
- ❌ Mở browser, đăng nhập OpenProject mỗi lần cần kiểm tra công việc
- ❌ Click từng trang để tạo task, phân công người, cập nhật trạng thái
- ❌ Nhớ ID của project, user, work package để làm việc
- ❌ Copy/paste dữ liệu giữa nhiều màn hình
- ❌ Làm thủ công các công việc lặp đi lặp lại

Giờ đây bạn có thể:
- ✅ **Nói chuyện tự nhiên** với Claude AI để quản lý công việc
- ✅ **Tự động hóa** các tác vụ phức tạp chỉ bằng 1 câu lệnh
- ✅ **Làm việc nhanh hơn 10 lần** so với thao tác thủ công
- ✅ **Không cần nhớ ID** - Claude tự tìm và xử lý
- ✅ **Xử lý hàng loạt** nhiều task cùng lúc

---

## 🚀 Cài Đặt Nhanh (10 phút)

### Bước 1: Cài Đặt Python và Git

1. **Kiểm tra Python** (cần Python 3.10 trở lên):
   ```bash
   python --version
   ```
   - Nếu chưa có, tải tại: https://www.python.org/downloads/
   - **Lưu ý Windows**: Tick vào "Add Python to PATH" khi cài đặt

2. **Kiểm tra Git**:
   ```bash
   git --version
   ```
   - Nếu chưa có, tải tại: https://git-scm.com/downloads

### Bước 2: Clone Project từ GitHub

1. **Mở Terminal/Command Prompt**

2. **Di chuyển đến thư mục muốn lưu project**:

   **Windows:**
   ```bash
   cd D:\Projects
   ```

   **Mac/Linux:**
   ```bash
   cd ~/Projects
   ```

3. **Clone repository**:
   ```bash
   git clone https://github.com/haunguyendev/openproject-mcp-server.git
   ```

4. **Di chuyển vào thư mục project**:
   ```bash
   cd openproject-mcp-server
   ```

5. **Lưu lại đường dẫn này** (bạn sẽ cần dùng sau):

   **Windows - Gõ lệnh:**
   ```bash
   cd
   ```
   Kết quả ví dụ: `D:\Projects\openproject-mcp-server`

   **Mac/Linux - Gõ lệnh:**
   ```bash
   pwd
   ```
   Kết quả ví dụ: `/Users/yourname/Projects/openproject-mcp-server`

### Bước 3: Cài Đặt Dependencies

1. **Cài đặt uv package manager**:

   **Windows (PowerShell):**
   ```powershell
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   **Mac/Linux:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Tạo virtual environment và cài đặt dependencies**:
   ```bash
   uv sync
   ```

   Lệnh này sẽ:
   - Tạo thư mục `.venv` (virtual environment)
   - Cài đặt tất cả packages cần thiết
   - Mất khoảng 1-2 phút

3. **Kiểm tra đã cài đặt thành công**:

   **Windows:**
   ```bash
   .venv\Scripts\python.exe --version
   ```

   **Mac/Linux:**
   ```bash
   .venv/bin/python --version
   ```

   Nếu thấy `Python 3.10.x` hoặc cao hơn → Thành công!

### Bước 4: Lấy API Key từ OpenProject

1. **Đăng nhập vào OpenProject** của bạn
2. Click vào **avatar** (góc trên bên phải)
3. Chọn **My account** → **Access tokens**
4. Click **+ Create** → Đặt tên (ví dụ: "Claude AI") → **Save**
5. **Copy** API key (chỉ hiện 1 lần duy nhất!)

### Bước 5: Lấy Đường Dẫn Python Chính Xác

Đây là bước quan trọng để cấu hình MCP!

**Windows - Mở Command Prompt trong thư mục project, gõ:**
```bash
echo %CD%\.venv\Scripts\python.exe
```
**Copy kết quả**, ví dụ:
```
D:\Projects\openproject-mcp-server\.venv\Scripts\python.exe
```

**Mac/Linux - Mở Terminal trong thư mục project, gõ:**
```bash
echo $PWD/.venv/bin/python
```
**Copy kết quả**, ví dụ:
```
/Users/yourname/Projects/openproject-mcp-server/.venv/bin/python
```

### Bước 6: Lấy Đường Dẫn File Server

**Windows - Gõ:**
```bash
echo %CD%\openproject-mcp-fastmcp.py
```
**Copy kết quả**, ví dụ:
```
D:\Projects\openproject-mcp-server\openproject-mcp-fastmcp.py
```

**Mac/Linux - Gõ:**
```bash
echo $PWD/openproject-mcp-fastmcp.py
```
**Copy kết quả**, ví dụ:
```
/Users/yourname/Projects/openproject-mcp-server/openproject-mcp-fastmcp.py
```

### Bước 7: Tải và Cài Claude Desktop

1. **Tải Claude Desktop**:
   - Truy cập: https://claude.ai/download
   - Tải và cài đặt phiên bản cho Windows/Mac

2. **Khởi động Claude Desktop** (để tạo file config)

3. **Đóng Claude Desktop** (chuẩn bị chỉnh sửa config)

### Bước 8: Cấu Hình Claude Desktop

1. **Tìm file cấu hình**:

   **Windows - Cách nhanh:**
   - Nhấn `Windows + R`
   - Gõ: `%APPDATA%\Claude`
   - Nhấn Enter
   - Tìm file `claude_desktop_config.json`

   **Mac - Cách nhanh:**
   - Mở Finder
   - Nhấn `Cmd + Shift + G`
   - Gõ: `~/Library/Application Support/Claude`
   - Nhấn Go
   - Tìm file `claude_desktop_config.json`

2. **Mở file bằng text editor** (Notepad, VS Code, v.v.)

3. **Dán cấu hình này vào**:

   **Ví dụ cho Windows:**
   ```json
   {
     "mcpServers": {
       "openproject": {
         "command": "D:\\Projects\\openproject-mcp-server\\.venv\\Scripts\\python.exe",
         "args": ["D:\\Projects\\openproject-mcp-server\\openproject-mcp-fastmcp.py"],
         "env": {
           "OPENPROJECT_URL": "https://your-company.openproject.com",
           "OPENPROJECT_API_KEY": "paste-your-api-key-here"
         }
       }
     }
   }
   ```

   **Ví dụ cho Mac/Linux:**
   ```json
   {
     "mcpServers": {
       "openproject": {
         "command": "/Users/yourname/Projects/openproject-mcp-server/.venv/bin/python",
         "args": ["/Users/yourname/Projects/openproject-mcp-server/openproject-mcp-fastmcp.py"],
         "env": {
           "OPENPROJECT_URL": "https://your-company.openproject.com",
           "OPENPROJECT_API_KEY": "paste-your-api-key-here"
         }
       }
     }
   }
   ```

4. **Thay thế các giá trị:**

   ✏️ Thay `command` bằng **đường dẫn Python** từ **Bước 5**

   ✏️ Thay `args` bằng **đường dẫn file server** từ **Bước 6**

   ✏️ Thay `OPENPROJECT_URL` bằng URL OpenProject của bạn (ví dụ: `https://mycompany.openproject.com`)

   ✏️ Thay `OPENPROJECT_API_KEY` bằng API key từ **Bước 4**

5. **Lưu file** và đóng text editor

### Bước 9: Kiểm Tra Kết Nối

1. **Khởi động lại Claude Desktop**

2. **Kiểm tra MCP server đã load**:
   - Nhìn góc dưới bên phải của Claude Desktop
   - Nếu thấy biểu tượng 🔌 hoặc số lượng tools → Đã kết nối!

3. **Test kết nối**:
   - Gõ: `Test kết nối với OpenProject`
   - Nếu thấy ✅ và thông tin phiên bản → **Thành công!**

4. **Test chức năng**:
   ```
   Cho tôi xem tất cả projects
   ```
   - Nếu thấy danh sách projects → **Hoàn hảo!**

### ⚠️ Nếu Gặp Lỗi

**Lỗi "Command not found" hoặc "File not found":**
- ✅ Kiểm tra lại đường dẫn Python (Bước 5)
- ✅ Kiểm tra lại đường dẫn file server (Bước 6)
- ✅ Đảm bảo dùng dấu `\\` trên Windows (không phải `/`)
- ✅ Đảm bảo dùng dấu `/` trên Mac/Linux (không phải `\\`)

**Lỗi "401 Unauthorized":**
- ✅ Kiểm tra lại API key có đúng không
- ✅ Kiểm tra API key còn hoạt động không (vào OpenProject xem)

**Lỗi "Connection refused":**
- ✅ Kiểm tra OPENPROJECT_URL có đúng không
- ✅ Thử truy cập URL đó bằng browser xem có mở được không

**Claude Desktop không nhận MCP:**
- ✅ Kiểm tra file JSON có đúng format không (dùng https://jsonlint.com)
- ✅ Restart lại máy tính
- ✅ Cài đặt lại Claude Desktop

---

## 💼 Các Tình Huống Thực Tế

### 🎯 Tình Huống 1: Sáng Thứ Hai - Xem Tổng Quan Công Việc

**Trước đây (thủ công):**
1. Mở browser → Đăng nhập OpenProject
2. Click vào từng project để xem task
3. Lọc task theo người, theo status
4. Copy danh sách vào email/chat để báo cáo

**Bây giờ (với Claude):**

```
Cho tôi xem tổng quan công việc tuần này:
- Tất cả task đang mở trong project "Website Redesign"
- Task nào quá hạn
- Task nào chưa có người nhận
```

**Claude sẽ tự động:**
- ✅ Tìm project theo tên
- ✅ Lọc task đang active
- ✅ Phân tích deadline
- ✅ Liệt kê task chưa assign
- ✅ Tạo báo cáo dễ đọc

### 🎯 Tình Huống 2: Tạo Sprint Mới Cho Team

**Trước đây (thủ công):**
1. Tạo từng task một trên web
2. Nhập tên, mô tả, priority
3. Assign từng người
4. Set deadline cho từng task
5. Tạo quan hệ phụ thuộc giữa các task

**Bây giờ (với Claude):**

```
Tạo sprint mới cho project "Mobile App" với các task:

1. Task cha: "User Authentication Module"
   - Assign cho Minh
   - Priority: High
   - Deadline: 20/01/2025

2. Các task con:
   - "Design login UI" → Assign Lan, deadline 10/01
   - "Implement API integration" → Assign Hùng, deadline 15/01
   - "Write unit tests" → Assign Nam, deadline 18/01

Tạo quan hệ: Task 2 phải xong trước khi bắt đầu task 3
```

**Claude sẽ tự động:**
- ✅ Tìm project "Mobile App"
- ✅ Tạo task cha và 3 task con
- ✅ Gán đúng người (tự tìm user ID)
- ✅ Set priority và deadline
- ✅ Tạo quan hệ parent-child
- ✅ Tạo dependency "follows"
- ✅ Báo cáo kết quả với ID của từng task

**Tiết kiệm:** Từ 15 phút → 30 giây!

### 🎯 Tình Huống 3: Phân Công Công Việc Mới

**Trước đây (thủ công):**
1. Tìm ID của người cần assign
2. Tìm task cần phân công
3. Update từng task một

**Bây giờ (với Claude):**

```
Trong project "Website Redesign", assign tất cả task về
"Frontend Development" cho Lan, và tất cả task về
"Backend API" cho Hùng
```

**Claude sẽ:**
- ✅ Tìm tất cả task liên quan
- ✅ Tự động assign theo yêu cầu
- ✅ Báo cáo số lượng task đã phân công

### 🎯 Tình Huống 4: Theo Dõi Tiến Độ Team

**Trước đây (thủ công):**
1. Vào từng project
2. Click vào từng member
3. Xem task của từng người
4. Tính toán thống kê thủ công

**Bây giờ (với Claude):**

```
Tạo báo cáo tiến độ team:
1. Minh đã hoàn thành bao nhiêu task tuần này?
2. Lan đang làm task nào?
3. Ai có nhiều task quá hạn nhất?
4. Tổng số giờ làm việc của team trong tháng 12
```

**Claude phân tích và trả lời tất cả trong 1 lần!**

### 🎯 Tình Huống 5: Quản Lý Thời Gian Làm Việc

**Trước đây (thủ công):**
1. Nhớ task nào đã làm bao nhiêu giờ
2. Vào từng task để log time
3. Chọn activity, nhập giờ

**Bây giờ (với Claude):**

```
Log thời gian làm việc hôm nay:
- Task #123: 3 giờ Development
- Task #124: 2 giờ Testing
- Task #125: 1.5 giờ Specification
```

**Hoặc hàng loạt:**

```
Xem tổng thời gian team đã làm trong project "Mobile App"
từ 01/12 đến 15/12
```

### 🎯 Tình Huống 6: Tạo Milestone và Phân Bổ Task

**Trước đây (thủ công):**
1. Tạo version/milestone
2. Vào từng task để gán milestone
3. Update deadline cho phù hợp

**Bây giờ (với Claude):**

```
Tạo milestone "Version 2.0 Release" cho project "Mobile App":
- Start date: 01/01/2025
- Due date: 31/03/2025
- Status: Open

Sau đó gán tất cả task có tag "v2.0" vào milestone này
```

### 🎯 Tình Huống 7: Quản Lý Quyền Truy Cập

**Trước đây (thủ công):**
1. Vào project settings
2. Click Members
3. Add từng người, chọn role

**Bây giờ (với Claude):**

```
Thêm các member mới vào project "Website Redesign":
- Email: newdev@company.com → Role: Developer
- Email: designer@company.com → Role: Designer
- Email: tester@company.com → Role: QA

Gửi notification khi thêm xong
```

### 🎯 Tình Huống 8: Xử Lý Task Quá Hạn Hàng Loạt

**Trước đây (thủ công):**
1. Tìm tất cả task quá hạn
2. Update deadline từng cái
3. Thông báo cho người liên quan

**Bây giờ (với Claude):**

```
Tìm tất cả task quá hạn trong project "Mobile App",
gia hạn thêm 1 tuần và thêm comment "Extended due to
holiday season" vào mỗi task
```

---

## 🛠️ 40 Công Cụ Có Sẵn

### 📊 1. Quản Lý Dự Án (7 công cụ)

#### ✅ `test_connection` - Kiểm tra kết nối
**Khi nào dùng:** Kiểm tra xem MCP server có hoạt động không

**Ví dụ:**
```
Test kết nối OpenProject
```

#### 📋 `list_projects` - Xem danh sách dự án
**Khi nào dùng:** Xem tất cả project bạn có quyền truy cập

**Ví dụ:**
```
Cho tôi xem tất cả project đang active
```
```
List tất cả project kể cả archived
```

#### 🔍 `get_project` - Xem chi tiết dự án
**Khi nào dùng:** Xem thông tin đầy đủ của 1 project

**Ví dụ:**
```
Cho tôi xem chi tiết project "Website Redesign"
```

#### ➕ `create_project` - Tạo dự án mới
**Khi nào dùng:** Khởi tạo project mới

**Ví dụ:**
```
Tạo project mới:
- Tên: "Mobile App v2.0"
- Identifier: mobile-app-v2
- Mô tả: Phát triển phiên bản mobile app thế hệ mới
- Public: No
```

#### ✏️ `update_project` - Cập nhật dự án
**Khi nào dùng:** Sửa thông tin project

**Ví dụ:**
```
Đổi tên project "Old Name" thành "New Name" và
update mô tả thành "Updated description"
```

#### 🗑️ `delete_project` - Xóa dự án
**Khi nào dùng:** Xóa project không còn dùng (cẩn thận!)

**Ví dụ:**
```
Xóa project "Test Project" (tôi chắc chắn muốn xóa)
```

#### 🔐 `check_permissions` - Kiểm tra quyền
**Khi nào dùng:** Xem bạn có những quyền gì

**Ví dụ:**
```
Check xem tôi có quyền gì trong OpenProject
```

---

### 📝 2. Quản Lý Công Việc (8 công cụ)

#### 📋 `list_work_packages` - Xem danh sách task
**Khi nào dùng:** Xem task trong project hoặc toàn bộ hệ thống

**Ví dụ:**
```
Xem tất cả task đang open trong project "Mobile App"
```
```
Xem task đã đóng của project ID 5
```
```
Xem 50 task mới nhất (có phân trang)
```

**Tham số:**
- `project_id`: ID của project (không bắt buộc)
- `active_only`: true = chỉ task đang mở, false = tất cả (mặc định: true)
- `offset`: Vị trí bắt đầu cho phân trang (mặc định: 0)
- `page_size`: Số lượng kết quả mỗi trang (mặc định: 20, tối đa: 100)

#### 🔍 `get_work_package` - Xem chi tiết task
**Khi nào dùng:** Xem đầy đủ thông tin của 1 task

**Ví dụ:**
```
Cho tôi xem chi tiết task #123
```

#### ➕ `create_work_package` - Tạo task mới
**Khi nào dùng:** Tạo công việc mới

**Ví dụ:**
```
Tạo task mới trong project "Website Redesign":
- Tên: "Fix responsive bug on mobile"
- Type: Bug
- Priority: High
- Assign: john@company.com
- Mô tả: "Responsive layout broken on iPhone 12"
- Deadline: 25/12/2024
```

**Tham số quan trọng:**
- `project_id`: ID dự án (bắt buộc)
- `subject`: Tiêu đề task (bắt buộc)
- `type_id`: Loại task (bắt buộc - xem bằng `list_types`)
- `description`: Mô tả chi tiết
- `priority_id`: Mức độ ưu tiên
- `assignee_id`: Người được giao việc
- `due_date`: Deadline (format: YYYY-MM-DD)
- `start_date`: Ngày bắt đầu
- `version_id`: Gán vào milestone/version

#### ✏️ `update_work_package` - Cập nhật task
**Khi nào dùng:** Sửa thông tin task, đổi status, reassign

**Ví dụ:**
```
Update task #123:
- Đổi status thành "In Progress"
- Assign cho Minh
- Set tiến độ 50%
- Gia hạn deadline đến 30/12/2024
```

**Tham số:**
- `work_package_id`: ID task (bắt buộc)
- `subject`: Tiêu đề mới
- `description`: Mô tả mới
- `status_id`: Trạng thái mới
- `assignee_id`: Người mới
- `priority_id`: Ưu tiên mới
- `percentage_done`: Tiến độ (0-100)
- `due_date`: Deadline mới
- `version_id`: Gán vào milestone khác

#### 🗑️ `delete_work_package` - Xóa task
**Khi nào dùng:** Xóa task không cần thiết

**Ví dụ:**
```
Xóa task #456
```

#### 🏷️ `list_types` - Xem loại task
**Khi nào dùng:** Xem có những loại task nào (Task, Bug, Feature...)

**Ví dụ:**
```
Cho tôi xem tất cả các loại work package
```
```
Xem types có trong project "Mobile App"
```

#### 📊 `list_statuses` - Xem trạng thái
**Khi nào dùng:** Xem có những status nào (New, In Progress, Closed...)

**Ví dụ:**
```
List tất cả status có thể dùng
```

#### 🎯 `list_priorities` - Xem mức độ ưu tiên
**Khi nào dùng:** Xem có những priority nào (Low, Normal, High, Immediate)

**Ví dụ:**
```
Cho tôi xem các mức priority
```

---

### 🌳 3. Quản Lý Cấu Trúc Task (3 công cụ)

#### 🔗 `set_work_package_parent` - Tạo task con
**Khi nào dùng:** Tạo quan hệ cha-con giữa các task

**Ví dụ:**
```
Đặt task #125, #126, #127 làm con của task #120
```

**Giải thích:**
- Task cha = Epic/Feature lớn
- Task con = Subtask nhỏ hơn

#### ✂️ `remove_work_package_parent` - Tách task con
**Khi nào dùng:** Làm task con thành task độc lập

**Ví dụ:**
```
Xóa quan hệ parent của task #125 (làm nó thành task độc lập)
```

#### 👶 `list_work_package_children` - Xem task con
**Khi nào dùng:** Xem tất cả subtask của 1 task cha

**Ví dụ:**
```
Cho tôi xem tất cả task con của task #120
```
```
Xem tất cả descendants (cháu, chắt) của task #100
```

**Tham số:**
- `work_package_id`: ID task cha (bắt buộc)
- `offset`: Phân trang
- `page_size`: Số lượng kết quả (mặc định: 20)

---

### 🔗 4. Quản Lý Quan Hệ Task (5 công cụ)

#### ➕ `create_work_package_relation` - Tạo quan hệ
**Khi nào dùng:** Tạo dependency giữa các task

**Các loại quan hệ:**
- **blocks**: Task A chặn task B (B không thể làm khi A chưa xong)
- **follows**: Task A theo sau B (B phải xong trước khi A bắt đầu)
- **precedes**: Task A đi trước B (A phải xong trước khi B bắt đầu)
- **relates**: Task A liên quan đến B (chung chủ đề)
- **duplicates**: Task A trùng với B
- **requires**: Task A cần task B
- **includes**: Task A bao gồm B
- **partof**: Task A là một phần của B

**Ví dụ:**
```
Tạo relation: task #123 phải xong trước khi task #124 bắt đầu
(type: precedes, lag: 2 ngày)
```
```
Đánh dấu task #130 duplicate task #125
```

**Tham số:**
- `from_id`: Task nguồn (bắt buộc)
- `to_id`: Task đích (bắt buộc)
- `type`: Loại quan hệ (bắt buộc)
- `lag`: Số ngày đệm (cho follows/precedes)
- `description`: Mô tả quan hệ

#### 📋 `list_work_package_relations` - Xem quan hệ
**Khi nào dùng:** Xem task liên quan đến những task nào

**Ví dụ:**
```
Xem tất cả relations của task #123
```

#### 🔍 `get_work_package_relation` - Chi tiết quan hệ
**Khi nào dùng:** Xem chi tiết 1 relation cụ thể

**Ví dụ:**
```
Xem chi tiết relation #45
```

#### ✏️ `update_work_package_relation` - Sửa quan hệ
**Khi nào dùng:** Đổi loại relation hoặc lag

**Ví dụ:**
```
Update relation #45: đổi lag thành 5 ngày
```

#### 🗑️ `delete_work_package_relation` - Xóa quan hệ
**Khi nào dùng:** Hủy bỏ dependency

**Ví dụ:**
```
Xóa relation #45
```

---

### 👥 5. Quản Lý Người Dùng (6 công cụ)

#### 👤 `list_users` - Xem danh sách user
**Khi nào dùng:** Xem tất cả user trong hệ thống

**Ví dụ:**
```
List tất cả user đang active
```
```
Tìm user có tên "Minh"
```

**Tham số:**
- `name`: Tìm theo tên (không bắt buộc)
- `status`: Lọc theo status (active, locked...)

#### 🔍 `get_user` - Xem chi tiết user
**Khi nào dùng:** Xem thông tin đầy đủ của 1 người

**Ví dụ:**
```
Cho tôi xem thông tin của user ID 5
```
```
Xem chi tiết user john@company.com
```

#### 🎭 `list_roles` - Xem vai trò
**Khi nào dùng:** Xem có những role nào (Admin, Developer, Manager...)

**Ví dụ:**
```
List tất cả roles trong hệ thống
```

#### 🔍 `get_role` - Chi tiết vai trò
**Khi nào dùng:** Xem quyền hạn của 1 role

**Ví dụ:**
```
Xem chi tiết role "Developer" (ID 3)
```

#### 👥 `list_project_members` - Xem thành viên project
**Khi nào dùng:** Xem ai đang tham gia project

**Ví dụ:**
```
Cho tôi xem tất cả members trong project "Mobile App"
```

#### 📂 `list_user_projects` - Xem project của user
**Khi nào dùng:** Xem 1 người đang tham gia project nào

**Ví dụ:**
```
Xem Minh đang làm trong những project nào
```

---

### 🔐 6. Quản Lý Phân Quyền (5 công cụ)

#### 📋 `list_memberships` - Xem membership
**Khi nào dùng:** Xem quan hệ user-project-role

**Ví dụ:**
```
Xem tất cả memberships trong project "Website"
```
```
Xem user Minh có membership nào
```

**Tham số:**
- `project_id`: Lọc theo project
- `user_id`: Lọc theo user

#### 🔍 `get_membership` - Chi tiết membership
**Khi nào dùng:** Xem chi tiết quyền của 1 người trong 1 project

**Ví dụ:**
```
Xem chi tiết membership #78
```

#### ➕ `create_membership` - Thêm thành viên
**Khi nào dùng:** Thêm người vào project với role cụ thể

**Ví dụ:**
```
Thêm user john@company.com vào project "Mobile App"
với role Developer (ID 3)
```
```
Thêm user ID 5 vào project "Website" với roles
Developer và Tester
```

**Tham số:**
- `project_id`: Project (bắt buộc)
- `user_id`: User ID (bắt buộc nếu không có group_id)
- `group_id`: Group ID (bắt buộc nếu không có user_id)
- `role_ids`: Danh sách role IDs (array)
- `role_id`: 1 role ID (thay vì array)
- `notification_message`: Tin nhắn gửi cho user

#### ✏️ `update_membership` - Sửa quyền
**Khi nào dùng:** Đổi role của người trong project

**Ví dụ:**
```
Update membership #78: đổi role thành Project Manager
```

#### 🗑️ `delete_membership` - Xóa thành viên
**Khi nào dùng:** Loại người khỏi project

**Ví dụ:**
```
Xóa membership #78 (remove user khỏi project)
```

---

### ⏱️ 7. Quản Lý Thời Gian (5 công cụ)

#### 📋 `list_time_entries` - Xem time log
**Khi nào dùng:** Xem giờ làm việc đã log

**Ví dụ:**
```
Xem tất cả time entries của task #123
```
```
Xem giờ làm việc của Minh từ 01/12 đến 15/12
```

**Tham số:**
- `work_package_id`: Lọc theo task
- `user_id`: Lọc theo user
- `from_date`: Từ ngày (YYYY-MM-DD)
- `to_date`: Đến ngày (YYYY-MM-DD)

#### ➕ `create_time_entry` - Log giờ làm việc
**Khi nào dùng:** Ghi nhận thời gian làm việc

**Ví dụ:**
```
Log time cho task #123:
- 3.5 giờ Development
- Ngày: 15/12/2024
- Comment: "Implemented user authentication"
```

**Activity IDs:**
- **1 = Management**: Quản lý, họp, planning
- **2 = Specification**: Viết tài liệu, requirements
- **3 = Development**: Code, implement
- **4 = Testing**: Test, QA, debug

**Tham số:**
- `work_package_id`: Task ID (bắt buộc)
- `hours`: Số giờ, VD: 2.5 (bắt buộc)
- `spent_on`: Ngày làm việc YYYY-MM-DD (bắt buộc)
- `activity_id`: Loại công việc 1-4 (bắt buộc)
- `comment`: Ghi chú

#### ✏️ `update_time_entry` - Sửa time log
**Khi nào dùng:** Sửa giờ đã log (nhầm giờ, sai activity)

**Ví dụ:**
```
Update time entry #234: đổi từ 2 giờ thành 3 giờ
```

#### 🗑️ `delete_time_entry` - Xóa time log
**Khi nào dùng:** Xóa time log nhập nhầm

**Ví dụ:**
```
Xóa time entry #234
```

#### 📊 `list_time_entry_activities` - Xem loại activity
**Khi nào dùng:** Xem có những activity nào để log time

**Ví dụ:**
```
List tất cả time entry activities
```

**Lưu ý:** Tool này có thể trả về lỗi 404 trên một số instance, nhưng các activity ID 1-4 vẫn hoạt động bình thường khi tạo time entry.

---

### 🎯 8. Quản Lý Milestone (2 công cụ)

#### 📋 `list_versions` - Xem milestone
**Khi nào dùng:** Xem các version/milestone của project

**Ví dụ:**
```
Xem tất cả versions trong project "Mobile App"
```

#### ➕ `create_version` - Tạo milestone mới
**Khi nào dùng:** Tạo version/milestone để gom nhóm task

**Ví dụ:**
```
Tạo version mới trong project "Mobile App":
- Tên: "Version 2.0"
- Start date: 01/01/2025
- Due date: 31/03/2025
- Status: Open
- Description: "Major update with new features"
```

**Tham số:**
- `project_id`: Project ID (bắt buộc)
- `name`: Tên version (bắt buộc)
- `description`: Mô tả
- `start_date`: Ngày bắt đầu (YYYY-MM-DD)
- `due_date`: Deadline (YYYY-MM-DD)
- `status`: Trạng thái (open, locked, closed)

---

## 🎓 Tips & Tricks Nâng Cao

### 💡 Tip 1: Tự Động Hóa Công Việc Lặp Lại

**Tạo template sprint:**
```
Mỗi thứ 2 đầu tuần, tạo sprint mới trong project "Mobile App" với:
- 1 task Planning meeting (assign cho PM)
- 1 task Code review session (assign cho Tech Lead)
- 1 task Team sync (assign toàn bộ team)

Tất cả đều deadline là thứ 6 tuần đó
```

### 💡 Tip 2: Batch Operations

**Xử lý hàng loạt:**
```
Tìm tất cả task:
- Trong project "Old Project"
- Status là "New" hoặc "In Progress"
- Chưa có assignee

Sau đó:
- Chuyển sang project "New Project"
- Assign cho Minh
- Set priority là Normal
```

### 💡 Tip 3: Smart Reporting

**Báo cáo thông minh:**
```
Tạo báo cáo tuần cho project "Mobile App":
1. Tổng số task completed tuần này
2. Tổng giờ làm việc của team
3. Top 3 người hoàn thành nhiều task nhất
4. Task nào blocked và lý do
5. Task nào quá hạn cần ưu tiên
```

### 💡 Tip 4: Dependency Management

**Quản lý phụ thuộc phức tạp:**
```
Tạo chuỗi task phụ thuộc cho feature "User Login":
1. "Design UI mockup" (3 ngày)
2. "Implement frontend" follows step 1 với lag 1 ngày
3. "Create API endpoints" follows step 1 với lag 1 ngày
4. "Integrate frontend-backend" requires cả step 2 và 3
5. "Write tests" follows step 4
6. "Deploy to staging" follows step 5

Tất cả assign cho team và tính deadline tự động
```

### 💡 Tip 5: Conditional Actions

**Hành động có điều kiện:**
```
Nếu task #123 đã hoàn thành, tự động:
1. Đóng tất cả task con
2. Tạo task mới "Deploy to production"
3. Assign cho DevOps team
4. Notify team lead
```

### 💡 Tip 6: Cross-Project Management

**Quản lý đa dự án:**
```
Xem tổng quan tất cả projects tôi làm:
- Tasks được assign cho tôi (tất cả projects)
- Deadline trong 3 ngày tới
- Priority High hoặc Immediate
- Sắp xếp theo deadline

Tạo checklist ưu tiên cho tôi
```

---

## ⚠️ Lưu Ý Quan Trọng

### 🔒 Về Quyền Hạn

**Cần quyền Admin/Manager cho:**
- Tạo/xóa project
- Quản lý user membership
- Xóa work package
- Tạo/sửa version

**Kiểm tra quyền trước khi thực hiện:**
```
Check permissions của tôi trước khi tạo project mới
```

### 💾 Về Backup

**Trước khi xóa hàng loạt:**
```
Trước khi xóa, hãy export danh sách tất cả task
trong project "Old Project" để backup
```

### 🎯 Về ID vs Tên

**Claude thông minh tự tìm ID:**
- ✅ "Assign cho Minh" → Claude tự tìm user ID
- ✅ "Project Website Redesign" → Claude tự tìm project ID
- ✅ "Status In Progress" → Claude tự tìm status ID

**Nhưng nếu cần chính xác:**
- Dùng ID trực tiếp: "task #123", "user ID 5", "project ID 10"

### ⏱️ Về Phân Trang

**Khi có nhiều kết quả:**
```
Xem 100 task mới nhất (page_size: 100)
```
```
Xem task từ vị trí 50 đến 100 (offset: 50, page_size: 50)
```

### 📅 Về Định Dạng Ngày

**Luôn dùng format ISO:**
- ✅ `2025-01-15` (YYYY-MM-DD)
- ❌ `15/01/2025`
- ❌ `Jan 15, 2025`

**Claude có thể convert:**
```
Set deadline task #123 là "15 tháng 1 năm 2025"
```
Claude sẽ tự convert sang `2025-01-15`

---

## 🆘 Xử Lý Sự Cố

### ❌ Lỗi "401 Unauthorized"

**Nguyên nhân:** API key sai hoặc hết hạn

**Cách khắc phục:**
1. Kiểm tra API key trong config
2. Tạo API key mới từ OpenProject
3. Update vào `claude_desktop_config.json`
4. Restart Claude Desktop

### ❌ Lỗi "403 Forbidden"

**Nguyên nhân:** Không có quyền thực hiện hành động

**Cách khắc phục:**
```
Check permissions của tôi
```
Sau đó liên hệ admin để cấp quyền

### ❌ Lỗi "404 Not Found"

**Nguyên nhân:**
- URL OpenProject sai
- Resource không tồn tại (task đã xóa, project không có...)

**Cách khắc phục:**
1. Kiểm tra URL trong config
2. Verify ID của resource
```
Tìm task có tên "Feature X" trong project "Mobile App"
```

### ❌ Không Kết Nối Được

**Checklist:**
1. ✅ OpenProject URL đúng?
2. ✅ API key đúng?
3. ✅ Network có hoạt động?
4. ✅ Proxy config đúng (nếu có)?
5. ✅ Restart Claude Desktop?

**Test connection:**
```
Test kết nối với OpenProject
```

### ❌ Claude Không Hiểu Yêu Cầu

**Tips viết câu lệnh tốt:**
- ✅ Rõ ràng: "Tạo task Bug trong project Mobile App"
- ❌ Mơ hồ: "Tạo cái gì đó"

- ✅ Chi tiết: "Assign task #123 cho john@company.com với deadline 20/12"
- ❌ Thiếu info: "Assign task"

- ✅ Có context: "Trong project Website, tìm task của Minh đang In Progress"
- ❌ Không context: "Tìm task"

---

## 📞 Hỗ Trợ & Phản Hồi

### 💬 Cần Trợ Giúp?

**Trong Claude Desktop:**
```
Tôi muốn [mô tả công việc], bạn có thể hướng dẫn tôi cách
dùng OpenProject tools không?
```

**Ví dụ:**
```
Tôi muốn tạo 1 sprint mới với 10 tasks và phân công cho
team, bạn có thể hướng dẫn từng bước không?
```

### 📝 Báo Lỗi

**GitHub Issues:**
https://github.com/AndyEverything/openproject-mcp-server/issues

**Thông tin cần có:**
1. Câu lệnh bạn đã dùng
2. Lỗi nhận được
3. Phiên bản OpenProject
4. Log (nếu có)

### 🌟 Góp Ý Cải Tiến

**GitHub Discussions:**
https://github.com/AndyEverything/openproject-mcp-server/discussions

---

## 📚 Tài Liệu Tham Khảo

- **README.md**: Tài liệu kỹ thuật đầy đủ
- **CLAUDE.md**: Hướng dẫn cho developer
- **OpenProject API v3**: https://www.openproject.org/docs/api/

---

## 🎉 Bắt Đầu Ngay!

Bây giờ bạn đã biết cách sử dụng, hãy thử ngay:

```
Cho tôi xem tất cả projects và tasks được assign cho tôi
có deadline trong tuần này
```

**Chúc bạn làm việc hiệu quả với OpenProject MCP Server! 🚀**

---

*Tài liệu được tạo bởi OpenProject MCP Server Team*
*Phiên bản: 1.0.0 | Cập nhật: 03/12/2024*
