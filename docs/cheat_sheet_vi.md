# ⚡ Cheat Sheet Chi Tiết: Các Câu Lệnh AI OpenProject

> **Copy-Paste và sửa lại phần in đậm cho phù hợp với tình huống của bạn!**

---

## 📋 1. Quản Lý Dự Án (Projects)

| Mục đích | Câu Lệnh Mẫu (Prompt) | Ví Dụ Thực Tế |
| :--- | :--- | :--- |
| **Tạo dự án mới** | "Tạo project mới tên là **[Tên]**, identifier là **[identifier]**. Mô tả: **[Mô Tả]**." | "Tạo project 'Website Redesign', identifier 'web-redesign'. Mô tả: 'Thiết kế lại website công ty'." |
| **Tạo dự án con** | "Tạo dự án con **[Tên Con]** (identifier: **[id-con]**)  thuộc dự án cha có ID **[ID Cha]**." | "Tạo dự án con 'Frontend' (identifier: 'frontend') thuộc dự án ID 5." |
| **Xem dự án con** | "Liệt kê tất cả dự án con của dự án ID **[ID]**." | "Liệt kê dự án con của dự án 'Website Redesign'." |
| **Xem cấu trúc phân cấp** | "Hiển thị danh sách dự án theo cấu trúc phân cấp." | *(Không cần sửa)* |
| **Thông tin dự án** | "Cho tôi thông tin chi tiết của dự án ID **[ID]** hoặc **[Tên]**." | "Chi tiết dự án 'Marketing Q4'." |
| **Cập nhật dự án** | "Update dự án ID **[ID]**: đổi tên thành **[Tên Mới]**, mô tả **[Mô Tả Mới]**." | "Update dự án ID 10: đổi tên 'Spring Campaign 2025'." |
| **Xoá dự án** | "Xoá dự án ID **[ID]**." | "Xoá dự án ID 12." |

---

## ✅ 2. Quản Lý Công Việc (Work Packages / Tasks)

### 2.1 Tạo & Tìm Kiếm
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Tạo task cơ bản** | "Tạo task **[Tên]** trong dự án **[Tên/ID]**, type **[Task/Bug/Feature]**." | "Tạo task 'Fix login bug' trong dự án 'Mobile App', type Bug." |
| **Tạo task với đầy đủ thông tin** | "Tạo task **[Tên]** trong dự án ID **[ID]**, gán cho user **[Tên]**, priority **[High/Normal/Low]**, deadline **[YYYY-MM-DD]**, description: **[Nội dung]**." | "Tạo task 'Design Homepage' trong dự án 5, gán cho Lan, priority High, deadline 2025-12-15." |
| **Tạo task con (child)** | "Tạo task con **[Tên Con]** cho task cha ID **[ID Cha]**." | "Tạo task con 'Design Header' cho task #50." |
| **Tìm task theo từ khoá** | "Tìm các task có chữ **'[Keyword]'** trong tiêu đề." | "Tìm task có chữ 'API' trong tiêu đề." |
| **Xem task của tôi** | "Liệt kê các task được gán cho tôi, trạng thái **Open**." | *(Copy nguyên)* |
| **Xem task theo dự án** | "Liệt kê tất cả task trong dự án **[Tên/ID]**, trạng thái **[open/closed/all]**." | "Liệt kê task trong dự án 'Website', trạng thái open." |

### 2.2 Cập Nhật Task
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Đổi trạng thái** | "Đổi trạng thái task #**[ID]** sang **[In Progress/Done/Closed]**." | "Đổi trạng thái task #123 sang Done." |
| **Đổi người nhận** | "Gán task #**[ID]** cho user **[Tên]**." | "Gán task #150 cho Hùng." |
| **Cập nhật nhiều trường** | "Update task #**[ID]**: trạng thái **[Status]**, tiến độ **[%]**, assignee **[Tên]**." | "Update task #200: trạng thái 'In Progress', tiến độ 50%, assignee Nam." |
| **Xoá task** | "Xoá task #**[ID]**." | "Xoá task #99." |

### 2.3 Quan Hệ Task (Relations)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Tạo quan hệ 'blocks'** | "Task #**[ID1]** blocks (chặn) task #**[ID2]**." | "Task #10 blocks task #20." |
| **Tạo quan hệ 'follows'** | "Task #**[ID1]** follows (theo sau) task #**[ID2]**." | "Task #30 follows task #25." |
| **Xem tất cả quan hệ** | "Liệt kê các quan hệ của task #**[ID]**." | "Liệt kê quan hệ của task #100." |

### 2.4 Phân Cấp Task (Hierarchy - Parent/Child)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Đặt task con** | "Đặt task #**[Child ID]** làm con của task #**[Parent ID]**." | "Đặt task #50 làm con của task #40." |
| **Xem danh sách task con** | "Liệt kê tất cả task con của task #**[Parent ID]**." | "Liệt kê task con của task #40." |
| **Xóa quan hệ cha-con** | "Xóa parent của task #**[Child ID]**." | "Xóa parent của task #50." |

### 2.5 🔍 Tìm Kiếm Nâng Cao (Advanced Filters)

| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Task quá hạn** | "Hiện task quá hạn trong dự án **[ID/Tên]**." | "Hiện task quá hạn trong dự án 18." |
| **Task sắp đến hạn** | "Hiện task sắp đến hạn trong **[N]** ngày tới." | "Hiện task đến hạn trong 3 ngày tới." |
| **Task chưa gán người** | "Hiện task chưa có người nhận trong dự án **[ID]**." | "Hiện task unassigned priority cao trong dự án 5." |
| **Task mới tạo** | "Hiện task được tạo trong **[N]** ngày gần đây." | "Hiện bug tạo trong 7 ngày qua." |
| **Task ưu tiên cao** | "Hiện tất cả task priority cao trong dự án **[ID]**." | "Hiện task ưu tiên cao trong dự án 18." |
| **Task gần hoàn thành** | "Hiện task > **[%]** %done." | "Hiện task >90% complete." |
| **Tìm kiếm linh hoạt** | "Tìm task **[điều kiện 1]** và **[điều kiện 2]** trong dự án **[ID]**." | "Tìm bug ưu tiên cao, quá hạn, chưa gán người trong dự án 5." |

**Ví Dụ Nâng Cao:**
- **Sprint Planning**: "Tìm task unassigned, priority cao trong sprint hiện tại" → chuẩn bị phân công
- **Daily Standup**: "Hiện task quá hạn của team" → theo dõi tiến độ
- **Weekly Review**: "Hiện bug tạo tuần này" → phân tích xu hướng
- **Sprint Cleanup**: "Tìm task 80-99% done" → chuẩn bị đóng sprint
- **Escalation**: "Tìm task quá hạn >5 ngày, priority cao, chưa gán người" → báo cáo khẩn cấp


---

## 👥 3. Quản Lý Người Dùng & Quyền (Users & Memberships)

| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Xem danh sách users** | "Liệt kê tất cả user đang active." | *(Copy nguyên)* |
| **Thông tin user** | "Thông tin chi tiết của user ID **[ID]** hoặc **[Tên]**." | "Thông tin user 'Nguyễn Văn A'." |
| **Thêm member vào dự án** | "Thêm user **[Tên/ID]** vào dự án **[Tên/ID]** với role **[Role ID/Tên]**." | "Thêm user 'Lan' vào dự án 'Mobile App' với role Developer." |
| **Xem members của dự án** | "Liệt kê tất cả members của dự án **[Tên/ID]**." | "Liệt kê members của dự án ID 8." |
| **Xem dự án của user** | "Liệt kê các dự án mà user **[Tên/ID]** tham gia." | "Liệt kê dự án của user 'Hùng'." |
| **Xoá member khỏi dự án** | "Xoá membership ID **[Membership ID]**." | "Xoá membership ID 55." |

---

## ⏱️ 4. Quản Lý Thời Gian (Time Tracking)

| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Log time** | "Log **[Số giờ]**h vào task #**[ID]**, ngày **[YYYY-MM-DD]**, ghi chú: **[Comment]**, activity: **[Development/Testing/Management]**." | "Log 4h vào task #123, ngày 2025-12-07, ghi chú: 'Code API', activity Development." |
| **Xem time entries của task** | "Liệt kê time entries của task #**[ID]**." | "Liệt kê time entries của task #50." |
| **Xem time entries của user** | "Liệt kê time entries của user **[Tên/ID]**." | "Liệt kê time entries của tôi." |
| **Update time entry** | "Update time entry ID **[ID]**: đổi số giờ thành **[Số]**h." | "Update time entry ID 200: đổi 3h." |
| **Xoá time entry** | "Xoá time entry ID **[ID]**." | "Xoá time entry ID 150." |

**Activity IDs phổ biến:**
- **1**: Management (Quản lý)
- **2**: Specification (Lập kế hoạch, tài liệu)
- **3**: Development (Code, lập trình)
- **4**: Testing (Kiểm thử)

---

## 📦 5. Phiên Bản / Milestone (Versions)

| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Tạo version mới** | "Tạo version **[Tên]** trong dự án **[ID]**, start date **[YYYY-MM-DD]**, end date **[YYYY-MM-DD]**." | "Tạo version 'Sprint 10' trong dự án 5, start 2025-12-01, end 2025-12-14." |
| **Xem versions** | "Liệt kê versions của dự án **[Tên/ID]**." | "Liệt kê versions của dự án 'Mobile App'." |

---

## 📊 6. Báo Cáo Tuần (Weekly Reports) - MỚI! ⚡

> **Tạo báo cáo tuần Agile/Scrum tự động từ OpenProject**

### 6.1 Báo Cáo Tự Động (Khuyến Nghị)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Báo cáo tuần này** | "Tạo báo cáo tuần này cho project **[ID]**, team **[Tên Team]**." | "Tạo báo cáo tuần này cho project 5, team Backend." |
| **Báo cáo tuần trước** | "Tạo báo cáo tuần trước cho project **[ID]**, team **[Tên]**." | "Tạo báo cáo tuần trước project 3, team Frontend." |
| **Báo cáo khoảng thời gian** | "Tạo báo cáo tuần project **[ID]** từ **[YYYY-MM-DD]** đến **[YYYY-MM-DD]**, team **[Tên]**, sprint goal **[Mục tiêu]**." | "Tạo báo cáo project 5 từ 2025-12-02 đến 2025-12-08, team Backend, sprint goal 'Complete authentication'." |

### 6.2 Lấy Dữ Liệu Để Customize
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Lấy raw data** | "Lấy dữ liệu báo cáo tuần project **[ID]** từ **[Start]** đến **[End]** dạng JSON." | "Lấy dữ liệu báo cáo project 5 từ 2025-12-02 đến 2025-12-08 dạng JSON." |
| **Custom report** | "Từ dữ liệu trên, tạo báo cáo với: **[Requirements]**." | "Từ dữ liệu trên, tạo executive summary 1 trang, chỉ metrics quan trọng." |

### 6.3 Hybrid - Bổ Sung Thông Tin
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Bổ sung chi tiết** | "Bổ sung vào báo cáo: **[1. Item 1, 2. Item 2, ...]**" | "Bổ sung: 1. List bugs đã fix, 2. Top 5 contributors, 3. Dependencies pending." |

**📋 Báo cáo tự động bao gồm 8 sections:**
- A. Thông tin chung (Project, Team, Sprint goal)
- B. Tóm tắt điều hành (Progress, Deliverables, Blockers)
- C. Delivery & Backlog (Done, In Progress, Planned, De-scoped)
- D. Nguồn lực & Năng lực (Team size, Hours logged, Distribution)
- E. Trở ngại & Phụ thuộc (Impediments, Dependencies)
- F. Chất lượng & Ổn định (Bugs, Test coverage, Incidents)
- G. Kế hoạch tuần tới (Top priorities)
- H. Sprint health & Cải tiến (Retro signals)

**💡 Tips:**
- Chạy vào thứ 6 chiều để có báo cáo tuần đầy đủ
- Bổ sung manual notes (sprint goal, retro insights)
- Export và share với team/leadership

---

## 📊 7. Báo Cáo Quản Lý - Dành Cho Sếp / PM

> **Các câu lệnh giúp nắm bắt tình hình dự án nhanh chóng, không cần vào từng task chi tiết**

### 7.1 Tổng Quan Dự Án (Project Overview)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Dashboard tổng hợp** | "Tóm tắt tình trạng dự án **[Tên/ID]**: Số task Open, In Progress, Done, Overdue." | "Tóm tắt dự án 'Website Redesign': task Open, Done, Overdue." |
| **Tiến độ hoàn thành** | "Dự án **[Tên/ID]** đã hoàn thành bao nhiêu % (phần trăm)?" | "Dự án 'Mobile App' hoàn thành bao nhiêu %?" |
| **Top vấn đề nổi bật** | "Liệt kê 5 task có priority cao nhất và chưa xong trong dự án **[Tên/ID]**." | "Top 5 task ưu tiên cao nhất chưa xong trong 'Marketing Q4'." |
| **Task quá hạn** | "Tìm tất cả task đã quá deadline trong dự án **[Tên/ID]**." | "Task overdue trong dự án 'Website'." |
| **Task không người nhận** | "Tìm task nào chưa được gán cho ai trong dự án **[Tên/ID]**." | "Task unassigned trong dự án ID 5." |
| **Task bị chặn (Blocked)** | "Tìm các task có trạng thái Blocked hoặc có quan hệ 'blocked by' trong dự án **[Tên/ID]**." | "Task đang bị block trong dự án 'Backend API'." |

### 7.2 Phân Tích Khối Lượng Công Việc (Workload Analysis)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Xem công việc của từng người** | "Liệt kê số lượng task Open của từng member trong dự án **[Tên/ID]**." | "Workload của từng người trong dự án 'Mobile App'." |
| **Ai đang quá tải?** | "Ai đang có nhiều task Open nhất trong dự án **[Tên/ID]**?" | "Member nào quá tải trong dự án 'Website'?" |
| **Ai đang rảnh?** | "Ai có ít task Open nhất (hoặc không có task) trong dự án **[Tên/ID]**?" | "Member nào đang rảnh trong dự án ID 8?" |
| **Time log của team** | "Tổng số giờ làm việc (time entries) của dự án **[Tên/ID]** trong tuần/tháng này." | "Tổng giờ làm việc của dự án 'Backend' tháng 12." |

### 7.3 So Sánh & Xu Hướng (Comparison & Trends)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **So sánh tiến độ nhiều dự án** | "So sánh tiến độ (% hoàn thành) của dự án **[ID1]** và dự án **[ID2]**." | "So sánh tiến độ dự án 'Frontend' và 'Backend'." |
| **Xu hướng task mới** | "Có bao nhiêu task mới được tạo trong dự án **[Tên/ID]** trong 7 ngày qua?" | "Task mới của dự án 'Mobile App' tuần này." |
| **Xu hướng hoàn thành** | "Có bao nhiêu task đã closed/done trong dự án **[Tên/ID]** trong tháng này?" | "Task hoàn thành của dự án 'Marketing' tháng 12." |

### 7.4 Báo Cáo Tổng Hợp (Executive Summary)
| Mục đích | Câu Lệnh Mẫu | Ví Dụ |
| :--- | :--- | :--- |
| **Báo cáo tổng thể** | "Viết báo cáo tổng hợp cho dự án **[Tên/ID]**: tiến độ, rủi ro, task overdue, và workload team." | "Báo cáo tổng hợp dự án 'Website Redesign'." |
| **Danh sách dự án đang active** | "Liệt kê tất cả dự án đang active và tiến độ % của từng dự án." | *(Copy nguyên)* |
| **Red flag (Cảnh báo)** | "Dự án nào đang có nhiều task overdue hoặc blocked? Ưu tiên cảnh báo." | *(Copy nguyên)* |

---

## 🔍 8. Tìm Kiếm & Báo Cáo Nâng Cao

| Scenario | Câu Lệnh |
| :--- | :--- |
| **Task quá hạn** | "Tìm các task đã quá hạn (overdue) trong dự án **[Tên]**." |
| **Task không có người nhận** | "Tìm các task chưa được gán cho ai (unassigned) trong dự án **[Tên]**." |
| **Task bị block** | "Tìm các task có quan hệ 'blocked' trong dự án **[Tên]**." |
| **Task ưu tiên cao** | "Liệt kê task có priority High trong dự án **[Tên]**, trạng thái Open." |
| **Báo cáo tổng hợp** | "Tóm tắt dự án **[Tên]**: Số task Open, Closed, In Progress, Overdue." |
| **Task gần deadline** | "Task nào của tôi sẽ hết hạn trong 7 ngày tới?" |

---

## 💡 Mẹo Sử Dụng Hiệu Quả

1. **Luôn cung cấp ID nếu có**: "Task #123" rõ ràng hơn "Task login".
2. **Dùng ngày chuẩn**: Format ngày là `YYYY-MM-DD` (VD: `2025-12-31`).
3. **Gộp nhiều lệnh**: "Tạo task A, sau đó log 2h vào task A."
4. **Hỏi trước khi xoá**: "Hiển thị thông tin task #100 trước khi xoá."
5. **Dùng filter**: "Liệt kê task Open của dự án X, gán cho user Y, priority High."

---

## 🆘 Xử Lý Lỗi Thường Gặp

| Lỗi | Giải Pháp |
| :--- | :--- |
| "Can't find project..." | Hỏi AI: "Liệt kê tất cả dự án" để lấy tên/ID chính xác. |
| "Permission denied" | Bạn không có quyền. Liên hệ Admin để cấp quyền. |
| "Invalid date format" | Dùng format `YYYY-MM-DD`. VD: `2025-12-31`. |
| AI hiểu sai | Tách thành nhiều câu nhỏ, từng bước một. |

---

**📌 Lưu tài liệu này để tra cứu nhanh!**
*Phòng Chuyển Đổi Số - [Tên Công Ty]*
