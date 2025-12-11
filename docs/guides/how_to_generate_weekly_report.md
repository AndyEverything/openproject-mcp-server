# Hướng dẫn: Tạo Báo cáo Tuần OpenProject

> Hướng dẫn chi tiết cách sử dụng Claude để tạo báo cáo tuần Agile/Scrum từ OpenProject

## Tổng quan

MCP OpenProject cung cấp **4 tools** để tạo báo cáo tuần:

1. **`generate_weekly_report`** - Tạo báo cáo đầy đủ (khuyến nghị)
2. **`get_report_data`** - Lấy raw data để tự customize
3. **`generate_this_week_report`** - Shortcut cho tuần này
4. **`generate_last_week_report`** - Shortcut cho tuần trước

---

## Cách 1: Sử dụng Tool Tự động (Nhanh nhất)

### Bước 1: Mở Claude Desktop

Đảm bảo MCP OpenProject đã được configure trong `claude_desktop_config.json`

### Bước 2: Chat với Claude

**Ví dụ 1: Báo cáo tuần này**
```
Tạo báo cáo tuần này cho project 5, team Backend
```

Claude sẽ tự động:
- Tính toán tuần hiện tại (Thứ 2 đến Chủ nhật)
- Lấy tất cả dữ liệu cần thiết
- Tạo báo cáo markdown đầy đủ 8 sections

**Ví dụ 2: Báo cáo tùy chỉnh khoảng thời gian**
```
Tạo báo cáo tuần cho:
- Project: 5
- Từ: 2025-12-02
- Đến: 2025-12-08
- Team: Backend Team Alpha
- Sprint goal: Complete authentication module
```

### Bước 3: Review và Export

- Claude trả về báo cáo markdown
- Copy vào file `.md` hoặc convert sang Word/PDF
- Share với team

**Thời gian:** ~10 giây ⚡

---

## Cách 2: Customize Báo cáo (Linh hoạt)

### Use Case: Cần format khác hoặc thêm analysis

**Bước 1: Lấy raw data**
```
Lấy dữ liệu báo cáo tuần project 5 từ 2025-12-02 đến 2025-12-08 dạng JSON
```

Claude gọi `get_report_data` và trả về JSON với:
```json
{
  "metadata": {...},
  "data": {
    "project": {...},
    "metrics": {
      "total_wps": 45,
      "done_count": 12,
      "in_progress_count": 8,
      ...
    },
    "work_packages": {
      "done": [...],
      "in_progress": [...],
      ...
    },
    "time_entries": [...],
    "members": [...]
  }
}
```

**Bước 2: Custom processing**
```
Từ dữ liệu này, tạo báo cáo với:
1. Chỉ giữ section A, B, C (bỏ các section khác)
2. Thêm biểu đồ pie chart phân bổ effort
3. Highlight top 3 contributors
4. Format ngắn gọn, dưới 1 trang
```

Claude sẽ process data và tạo báo cáo theo yêu cầu.

**Thời gian:** ~30-60 giây (tùy complexity)

---

## Cách 3: Hybrid - Kết hợp cả 2

### Workflow khuyến nghị cho Admin

**Bước 1: Tạo báo cáo base nhanh**
```
Tạo báo cáo tuần này project 5
```

**Bước 2: Bổ sung thông tin chi tiết**
```
Bổ sung vào báo cáo:
1. List tất cả bugs đã close (type=bug, status=closed)
2. Top 5 người log nhiều hours nhất
3. Dependencies còn pending
```

Claude sẽ gọi thêm tools:
- `list_work_packages` (filter bugs)
- `list_time_entries` (group by user)
- `list_relations` (check dependencies)

Và append vào báo cáo đã có.

---

## Cấu trúc Báo cáo

Báo cáo tự động tạo có **8 sections chính**:

### A. Thông tin chung
- Tuần báo cáo, Team/Squad
- Project/Module, Sprint Goal
- Links (tự động từ OpenProject)

### B. Tóm tắt điều hành
- Tiến độ: 🟢 On track / 🟡 At risk / 🔴 Off track
- Top 3 deliverables
- Vướng mắc, rủi ro
- Cần hỗ trợ

### C. Delivery & Backlog
**4 nhóm:**
- ✅ Done
- 🔄 In Progress
- 📋 Planned/Not Started
- ❌ De-scoped

Mỗi WP hiển thị: ID, subject, owner, ETA, status

### D. Nguồn lực & Năng lực
- Quy mô team (số members)
- Capacity (tổng hours logged)
- Phân bổ: Dev / QA / Management

### E. Trở ngại & Phụ thuộc
- Impediments (WPs bị blocked)
- Dependencies (từ relations)

### F. Chất lượng & Ổn định
- Bug phát sinh/đóng
- Test coverage (cần manual input)
- Incidents

### G. Kế hoạch tuần tới
- Top 5 priorities (từ planned WPs)
- Mục tiêu measurable

### H. Sprint Health & Cải tiến
- Retro signals
- Action items

### Phụ lục: Bản siêu gọn
- 1-page summary cho leadership
- Chỉ metrics quan trọng

---

## Tips & Best Practices

### ✅ Recommend

**1. Thời điểm tạo báo cáo**
- Cuối tuần (Thứ 6 chiều hoặc Chủ nhật)
- Sau sprint review/retro

**2. Workflow chuẩn**
```
Thứ 6 chiều:
1. Tạo báo cáo tuần này → Review
2. Bổ sung manual notes (sprint goal, retro)
3. Export và gửi team

Thứ 2 sáng:
4. Share trong stand-up
5. Archive vào wiki/Confluence
```

**3. Customize theo team**
- Backend team: Focus vào technical debt, code quality
- Frontend team: Focus vào UI bugs, user-facing features
- QA team: Focus vào test coverage, bug metrics

### ❌ Pitfalls

**1. Date ranges quá rộng**
```
❌ Tạo báo cáo tháng này (quá nhiều data, chậm)
✅ Tạo báo cáo tuần này (optimized)
```

**2. Không specify team/sprint goal**
```
❌ Tạo báo cáo project 5
✅ Tạo báo cáo project 5, team Backend, sprint goal "Auth module"
```

**3. Expect real-time data**
- OpenProject có thể có cache/delay
- Luôn check timestamp trong báo cáo

---

## Troubleshooting

### Vấn đề 1: Báo cáo trống

**Nguyên nhân:** Không có WPs updated trong date range

**Giải pháp:**
```
1. List all work packages project 5
2. Check xem có WPs nào không
3. Nếu có nhưng báo cáo trống → adjust date range
```

### Vấn đề 2: Thiếu time entries

**Nguyên nhân:** Team chưa log hours

**Giải pháp:**
- Nhắc team log time trước khi tạo báo cáo
- Hoặc tạo báo cáo mà không có section capacity

### Vấn đề 3: Tool chậm (>30s)

**Nguyên nhân:** Project quá lớn (>500 WPs)

**Giải pháp:**
```
1. Dùng get_report_data với filters cụ thể
2. Hoặc split report theo module/component
```

---

## Examples

### Example 1: Quick Weekly Report
```
User: "Tạo báo cáo tuần này project 5"

Claude: [Calls generate_this_week_report(5)]

Result: Markdown report (2025-12-02 to 2025-12-08)
  - 15 WPs done
  - 8 WPs in progress
  - 120.5 hours logged
  - 2 blockers
```

### Example 2: Custom Multi-Week Analysis
```
User: "So sánh 2 tuần gần nhất project 5"

Claude: 
  [Calls get_report_data(5, "2025-11-25", "2025-12-01")]
  [Calls get_report_data(5, "2025-12-02", "2025-12-08")]
  [Compares and creates custom analysis]
  
Result: Comparison report showing:
  - Velocity trend: ↗️ +20%
  - Bug rate: ↘️ -15%
  - Top performers
```

### Example 3: Executive Summary Only
```
User: "Tạo executive summary 1 trang cho leadership, project 5 tuần này"

Claude: 
  [Calls generate_this_week_report(5)]
  [Extracts only Phụ lục section]
  [Formats for 1-page view]

Result: Concise summary with key metrics only
```

---

## FAQ

**Q: Có thể tạo báo cáo cho nhiều projects cùng lúc?**

A: Có, dùng cách này:
```
Tạo báo cáo tổng hợp:
1. Báo cáo tuần này project 5
2. Báo cáo tuần này project 3
3. Merge highlights từ cả 2
```

**Q: Báo cáo có include comments/activities không?**

A: Hiện tại không auto include. Nếu cần, request thêm:
```
Bổ sung vào báo cáo:
- List activities của top 5 WPs quan trọng nhất
```

**Q: Export sang format khác (Word, PDF)?**

A: Báo cáo ra markdown. Sau đó:
- Copy vào Notion/Confluence (auto format)
- Dùng Pandoc convert: `pandoc report.md -o report.docx`
- Hoặc paste vào Google Docs

**Q: Lưu báo cáo ở đâu?**

A: Recommend:
- Git repo: `reports/weekly/2025-W49.md`
- Confluence: Weekly Reports space
- Email: Gửi team mỗi tuần

---

## Next Steps

1. ✅ Thử tạo báo cáo đầu tiên
2. 📝 Review và adjust template
3. 🔄 Setup workflow tự động
4. 📊 Tích hợp vào sprint ceremonies

Xem thêm:
- [Prompt Templates](prompts/weekly_report_vi.md)
- [Examples](examples/weekly_report_example.md)
- [Cheat Sheet](cheat_sheet_vi.md)
