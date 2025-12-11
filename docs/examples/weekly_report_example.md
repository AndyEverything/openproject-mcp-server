# Examples: Báo cáo Tuần OpenProject

> Ví dụ conversations thực tế với Claude để tạo báo cáo tuần

---

## Example 1: Quick Weekly Report (Cách đơn giản nhất)

### Conversation

**User:**
```
Tạo báo cáo tuần này cho project 5, team Backend
```

**Claude:**
```
[Calling tool: generate_this_week_report]
Parameters:
- project_id: 5
- team_name: "Backend"

Processing...
✅ Generated weekly report for 2025-12-02 to 2025-12-08
```

**Result:**
```markdown
# BÁO CÁO TUẦN - AGILE SCRUM

*Tự động tạo từ OpenProject*

## A. THÔNG TIN CHUNG

| Tuần báo cáo | Giá trị |
|--------------|---------|
| Từ ngày - Đến ngày | 2025-12-02 - 2025-12-08 |
| Team/Squad | Backend |
| Product/Module | E-commerce Platform |
| Project ID | #5 |
| Sprint Goal | N/A |

## B. TÓM TẮT ĐIỀU HÀNH

**Tiến độ so với Sprint Goal:** 🟢 On track

**Deliverables nổi bật (đã Done):**
1. #423 - Implement user authentication API
2. #425 - Fix payment gateway timeout issue
3. #427 - Add order history endpoint

**Vướng mắc lớn nhất:** Không có

**Cần hỗ trợ/quyết định:** _(Cần cập nhật thủ công)_

## C. DELIVERY & BACKLOG MOVEMENT

### 1) Công việc đã hoàn thành (Done)

| Ticket/Story | Mô tả ngắn | Owner | Ngày Done | Status |
|--------------|------------|-------|-----------|--------|
| [Feature #423] | Implement user authentication API | John Doe | 2025-12-05 | Closed |
| [Bug #425] | Fix payment gateway timeout issue | Jane Smith | 2025-12-06 | Closed |
| [Feature #427] | Add order history endpoint | John Doe | 2025-12-07 | Closed |

### 2) Công việc đang thực hiện (In Progress)

| Ticket/Story | Mô tả ngắn | Owner | ETA | Status |
|--------------|------------|-------|-----|--------|
| [Feature #430] | Implement shopping cart sync | Mike Johnson | 2025-12-10 | In Development |
| [Feature #432] | Add product search API | Sarah Lee | 2025-12-12 | In Development |

...
```

**Time:** ~8 seconds ⚡

---

## Example 2: Custom Report với Sprint Goal

### Conversation

**User:**
```
Tạo báo cáo tuần cho:
- Project: 3
- Từ: 2025-11-25
- Đến: 2025-12-01
- Team: Frontend Team
- Sprint goal: Complete checkout flow redesign
```

**Claude:**
```
[Calling tool: generate_weekly_report]
Parameters:
- project_id: 3
- from_date: "2025-11-25"
- to_date: "2025-12-01"
- team_name: "Frontend Team"
- sprint_goal: "Complete checkout flow redesign"
- format: "markdown"

Processing...
✅ Generated custom weekly report
```

**Result:**
Report với sprint goal được điền, tập trung analysis vào checkout flow

**Time:** ~10 seconds

---

## Example 3: Get Raw Data để Customize

### Conversation

**User:**
```
Lấy dữ liệu báo cáo tuần project 5 từ 2025-12-02 đến 2025-12-08 dạng JSON
```

**Claude:**
```
[Calling tool: get_report_data]
Parameters:
- project_id: 5
- from_date: "2025-12-02"
- to_date: "2025-12-08"

Processing...
✅ Retrieved report data
```

**Result:**
```json
{
  "metadata": {
    "project_id": 5,
    "from_date": "2025-12-02",
    "to_date": "2025-12-08",
    "generated_at": "2025-12-09T14:30:00",
    "work_packages_count": 23,
    "time_entries_count": 45,
    "members_count": 8
  },
  "data": {
    "project": {
      "id": 5,
      "name": "E-commerce Platform"
    },
    "metrics": {
      "total_wps": 23,
      "done_count": 8,
      "in_progress_count": 5,
      "planned_count": 7,
      "blocked_count": 0,
      "bug_count": 3,
      "feature_count": 18,
      "total_hours": 156.5,
      "dev_hours": 98.0,
      "qa_hours": 32.5,
      "management_hours": 26.0
    },
    "work_packages": {
      "done": [...],
      "in_progress": [...],
      "planned": [...]
    },
    ...
  }
}
```

**User:**
```
Từ dữ liệu này, tạo executive summary 1 trang với:
- Chỉ metrics quan trọng
- Top 3 achievements
- Top 3 risks
- Next week priorities
```

**Claude:**
```
[Analyzes JSON data and creates custom report]

# EXECUTIVE SUMMARY - Week of Dec 2-8, 2025
E-commerce Platform | Team: Backend

## 📊 Key Metrics
- ✅ Completed: 8 work packages (35% completion rate)
- 🔄 In Progress: 5 work packages  
- ⏱️ Effort: 156.5 hours (63% dev, 21% QA, 16% mgmt)
- 🐛 Bugs: 3 total (all resolved)

## 🎯 Top 3 Achievements
1. User authentication API fully implemented and tested
2. Payment gateway timeout fixed - response time improved 70%
3. Order history endpoint deployed to staging

## ⚠️ Top 3 Risks
1. Shopping cart sync delayed - dependencies on external API
2. Product search performance concerns with large catalogs
3. Two team members on leave next week - capacity reduced

## 📅 Next Week Priorities
1. Complete shopping cart sync (Mike - ETA Dec 12)
2. Product search optimization (Sarah - ETA Dec 15)
3. Begin inventory management module (Team - ETA Dec 20)
```

**Time:** ~45 seconds (processing + custom format)

---

## Example 4: Multi-Week Comparison

### Conversation

**User:**
```
So sánh 2 tuần gần nhất của project 5, tìm trends
```

**Claude:**
```
[Calls get_report_data for week 1: Nov 25 - Dec 1]
[Calls get_report_data for week 2: Dec 2 - Dec 8]

Analyzing trends...
```

**Result:**
```markdown
# Weekly Trend Analysis - Project 5

## Comparison: Week 1 vs Week 2

### Velocity
- Week 1 (Nov 25-Dec 1): 6 WPs completed
- Week 2 (Dec 2-Dec 8): 8 WPs completed
- **Trend:** ↗️ +33% improvement

### Effort
- Week 1: 142.0 hours
- Week 2: 156.5 hours
- **Trend:** ↗️ +10% increase

### Quality
- Week 1: 5 bugs reported
- Week 2: 3 bugs reported
- **Trend:** ↘️ -40% reduction

### Team Performance
Top performers (combined 2 weeks):
1. John Doe: 45.5 hours (mostly development)
2. Jane Smith: 38.0 hours (QA + bug fixes)
3. Mike Johnson: 32.5 hours (development)

### Insights
✅ **Positive:**
- Velocity improving steadily
- Bug rate decreasing
- Team capacity stable

⚠️ **Watch out:**
- Some WPs taking longer than estimated
- Need better sprint planning
```

**Time:** ~60 seconds (multiple API calls + analysis)

---

## Example 5: Hybrid Approach

### Conversation

**User:**
```
Tạo báo cáo tuần này project 5
```

**Claude:**
```
[Calls generate_this_week_report(5)]

✅ Generated base report
```

**User:**
```
Bổ sung thêm:
1. List tất cả bugs đã fix trong tuần
2. Top 5 người log nhiều hours nhất  
3. Dependencies còn pending
```

**Claude:**
```
[Calls list_work_packages with filters: type=bug, status=closed]
Found 3 bugs closed this week:
- #425: Payment timeout (High priority)
- #429: Cart not updating (Medium)
- #431: Email validation error (Low)

[Calls list_time_entries, groups by user]
Top 5 contributors:
1. John Doe: 24.5h
2. Jane Smith: 18.0h
3. Mike Johnson: 16.5h
4. Sarah Lee: 15.0h
5. Tom Wilson: 12.5h

[Calls list_relations for each in-progress WP]
Found 2 blocking dependencies:
- #430 blocked by external API (vendor)
- #432 blocked by database migration (#428)

Now appending to report...
```

**Result:**
Original report + 3 new sections with detailed data

**Time:** ~30 seconds (base + augmentation)

---

## Example 6: Troubleshooting Empty Report

### Conversation

**User:**
```
Tạo báo cáo tuần này project 7
```

**Claude:**
```
[Calls generate_this_week_report(7)]

⚠️ Warning: Report generated but appears empty
- 0 work packages found
- 0 time entries
```

**User:**
```
Kiểm tra xem có work packages nào trong project 7 không?
```

**Claude:**
```
[Calls list_work_packages for project 7]

Found 15 work packages, but none updated this week (Dec 2-8)

Possible reasons:
1. No activity this week
2. Team didn't update WP statuses
3. Using different project?
```

**User:**
```
List tất cả work packages project 7, không filter date
```

**Claude:**
```
[Calls list_work_packages(project_id=7, active_only=True)]

✅ Found 15 work packages:
- Last updates: mostly in November
- Suggests project may be inactive or on hold

Recommendation: 
- Check with PM if project 7 is current
- Or generate report for broader date range
```

**Solution:** User chọn project khác hoặc adjust date range

---

## Tips từ Examples

### 1. Start Simple
Luôn bắt đầu với prompt đơn giản:
```
Tạo báo cáo tuần này project X
```

### 2. Iterate khi cần
Sau khi có báo cáo base, bổ sung:
```
Bổ sung thêm: [specific requests]
```

### 3. Debug từng bước
Nếu có vấn đề:
```
1. Test connection
2. List work packages
3. Check date ranges
4. Verify project ID
```

### 4. Combine approaches
- Quick report → Review → Augment → Export

---

## Common Patterns

```
# Pattern 1: Weekly routine
Thứ 6 chiều: "Tạo báo cáo tuần này project 5"

# Pattern 2: Sprint review
Cuối sprint: "Tạo báo cáo từ [sprint start] đến [sprint end]"

# Pattern 3: Leadership update
"Tạo executive summary project 5, chỉ 1 trang"

# Pattern 4: Deep analysis
"Lấy data tuần này" → Custom analysis → "Tạo custom report"

# Pattern 5: Multi-project
"Tạo báo cáo project 3, 5, 7" → "Merge highlights"
```

---

Xem thêm:
- [User Guide](../guides/how_to_generate_weekly_report.md)
- [Prompt Templates](../prompts/weekly_report_vi.md)
