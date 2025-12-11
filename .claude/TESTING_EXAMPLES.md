# 🧪 OpenProject MCP Server - Testing Examples

Các câu hỏi ví dụ để test trên Claude Desktop với OpenProject MCP Server.

---

## 📋 Phase 1: Quick Wins - Daily Standup & Risk Detection

### 1. Daily Standup Report

**Câu hỏi cơ bản:**
```
Generate a daily standup report for today
```

**Câu hỏi cho user cụ thể:**
```
Generate daily standup report for user 7
```

**Câu hỏi tiếng Việt:**
```
Tạo báo cáo standup hôm nay cho tôi
```

**Kết quả mong đợi:**
- Danh sách công việc hoàn thành hôm qua
- Công việc đang làm
- Blocker nếu có
- Đề xuất công việc hôm nay
- Tổng thời gian làm việc

---

### 2. Detect Blockers & Risks

**Câu hỏi cơ bản:**
```
Check for blockers and risks in the current sprint
```

**Câu hỏi cho sprint cụ thể:**
```
Detect blockers and risks for sprint 5
```

**Câu hỏi cho project:**
```
Show me all risks in project 3
```

**Câu hỏi tiếng Việt:**
```
Kiểm tra các rủi ro và blocker trong sprint hiện tại
```

**Kết quả mong đợi:**
- Danh sách task quá hạn
- Task có nguy cơ cao (due soon, ít progress)
- Dependency blockers
- Thành viên bị overload
- Risk score tổng thể

---

### 3. Bulk Update Work Packages

**Câu hỏi cơ bản:**
```
Move tasks [123, 124, 125] to sprint 5
```

**Câu hỏi phức tạp:**
```
Update status of tasks [100, 101, 102] to closed and set percentage_done to 100
```

**Câu hỏi tiếng Việt:**
```
Chuyển 5 task này sang sprint 6: [201, 202, 203, 204, 205]
```

**Kết quả mong đợi:**
- Số lượng task cập nhật thành công
- Danh sách lỗi (nếu có)
- Success rate

---

## 🧠 Phase 2: Sprint Intelligence - AI-Powered Tools

### 4. Create Sprint

**Câu hỏi cơ bản:**
```
Create a new sprint named "Sprint 42" for project 5, from 2025-01-15 to 2025-01-29
```

**Câu hỏi có goal:**
```
Create sprint "Sprint 10" in project 3 from January 20 to February 3, 2025 with goal "Complete authentication module"
```

**Câu hỏi tiếng Việt:**
```
Tạo sprint mới tên "Sprint Q1.2025" cho project 2, từ ngày 1/1/2025 đến 14/1/2025, mục tiêu là "Hoàn thành tính năng thanh toán"
```

**Kết quả mong đợi:**
- Sprint ID
- Thời gian sprint
- Sprint goal
- Hướng dẫn bước tiếp theo

---

### 5. Get Sprint Status

**Câu hỏi cơ bản:**
```
Show me the status of sprint 5
```

**Câu hỏi chi tiết:**
```
Get detailed sprint status for sprint 10 with burndown data
```

**Câu hỏi tiếng Việt:**
```
Cho tôi xem tình trạng sprint 8 hiện tại
```

**Kết quả mong đợi:**
- Story points (completed/total)
- Task breakdown theo status
- Team progress
- Risk assessment
- Completion forecast
- Progress bar

---

### 6. AI Story Point Estimation

**Câu hỏi cơ bản:**
```
Estimate story points for work package #456
```

**Câu hỏi tiếng Việt:**
```
Ước tính story points cho task #789
```

**Kết quả mong đợi:**
- Story points đề xuất
- Confidence score (High/Medium/Low)
- Top 5 task tương tự
- Lý do đề xuất
- Keywords extracted

---

### 7. AI Dependency Detection

**Câu hỏi cơ bản:**
```
Detect dependencies between tasks [123, 124, 125, 126, 127]
```

**Câu hỏi tiếng Việt:**
```
Phân tích các phụ thuộc giữa các task trong sprint 5
```

**Kết quả mong đợi:**
- Existing dependencies
- AI-suggested dependencies với confidence score
- Critical path
- High-dependency tasks
- Recommendations

---

### 8. Auto-Assign Sprint Tasks

**Câu hỏi balanced strategy:**
```
Auto-assign unassigned tasks in sprint 5 using balanced strategy
```

**Câu hỏi skill-based:**
```
Assign sprint 6 tasks based on team member skills
```

**Câu hỏi priority-first:**
```
Assign tasks in sprint 7 with priority-first strategy
```

**Câu hỏi tiếng Việt:**
```
Tự động phân công các task chưa assign trong sprint 4, dùng chiến lược cân bằng
```

**Kết quả mong đợi:**
- Danh sách recommended assignments
- Team capacity summary
- Capacity warnings
- Bulk update commands

---

## 🎯 Advanced Testing Scenarios

### Scenario 1: Complete Sprint Planning

**Workflow:**
```
1. Create sprint "Sprint 15" in project 5 from Feb 1 to Feb 14, 2025
2. Show me sprint 15 status
3. Auto-assign tasks in sprint 15 with skill-based strategy
4. Detect blockers and risks for sprint 15
```

---

### Scenario 2: Daily Scrum Master Tasks

**Workflow:**
```
1. Generate daily standup report for today
2. Check for blockers in current sprint
3. Show me sprint status for sprint 8
```

---

### Scenario 3: Story Estimation Session

**Workflow:**
```
1. Estimate story points for task #123
2. Estimate story points for task #124
3. Estimate story points for task #125
4. Detect dependencies between tasks [123, 124, 125]
```

---

### Scenario 4: Sprint Transition

**Workflow:**
```
1. Get sprint status for sprint 5
2. Move incomplete tasks [201, 202, 203] to sprint 6
3. Mark completed tasks [100, 101, 102] as closed
4. Generate standup report
```

---

## 🌐 Vietnamese Testing Examples

### Các câu hỏi tiếng Việt phức tạp:

**Sprint Management:**
```
Tạo sprint mới cho tháng 1/2025, dự án số 3, kéo dài 2 tuần
```

**Daily Standup:**
```
Tạo báo cáo daily cho user số 5, tôi muốn xem công việc hôm qua và hôm nay
```

**Risk Detection:**
```
Kiểm tra xem sprint hiện tại có task nào bị trễ không, và ai đang bị quá tải
```

**Estimation:**
```
Ước tính xem task #456 cần bao nhiêu story points
```

**Assignment:**
```
Tự động chia task trong sprint 7 cho team, ưu tiên người có kỹ năng phù hợp
```

**Bulk Update:**
```
Chuyển tất cả task chưa làm xong trong sprint 5 sang sprint 6
```

---

## 🔍 Edge Cases to Test

### 1. Empty Sprint
```
Show me status of sprint 99 (empty sprint)
```

### 2. Overloaded Sprint
```
Detect risks in sprint 3 (sprint với nhiều task quá hạn)
```

### 3. No Similar Tasks
```
Estimate story points for task #999 (task hoàn toàn mới, không có similar tasks)
```

### 4. All Tasks Assigned
```
Auto-assign tasks in sprint 8 (sprint đã assign hết)
```

### 5. No Blockers
```
Detect blockers in sprint 10 (sprint không có blocker)
```

---

## 📊 Expected Response Patterns

### ✅ Success Response
- Bắt đầu với ✅ emoji
- Structured markdown format
- Clear sections với headers
- Actionable recommendations
- Next steps suggestions

### ❌ Error Response
- Bắt đầu với ❌ emoji
- Clear error message
- Helpful hints
- Suggestions để fix

### 🤖 AI Response
- Confidence scores
- Reasoning/explanation
- Similar examples
- Recommendations

---

## 🎮 Quick Test Commands

### Test all Phase 1 tools:
```
1. Generate daily standup report
2. Detect blockers and risks
3. Update tasks [1,2,3] to set status_id to 12
```

### Test all Phase 2 tools:
```
1. Create sprint "Test Sprint" in project 1 from today to +14 days
2. Get sprint status for sprint 1
3. Estimate story points for task #1
4. Detect dependencies in tasks [1,2,3,4,5]
5. Auto-assign tasks in sprint 1
```

---

## 💡 Pro Tips

1. **Luôn test với data thật**: Dùng project/sprint/task IDs thật từ OpenProject instance của bạn

2. **Test error cases**: Thử với IDs không tồn tại để xem error handling

3. **Test permissions**: Thử với user có quyền khác nhau

4. **Test large datasets**: Thử với sprint có nhiều tasks (>50)

5. **Test Vietnamese**: AI tools support tiếng Việt tốt, hãy thử!

6. **Combine tools**: Test workflows kết hợp nhiều tools

7. **Check consistency**: Chạy lại cùng một query nhiều lần để đảm bảo kết quả nhất quán

---

## 🐛 Known Limitations to Test

1. **Time Entry Activities**: Endpoint trả về 404 nhưng activities vẫn hoạt động với IDs 1-4
2. **Pagination**: Test với sprint có >100 tasks
3. **Story Points**: Một số OpenProject instance không có custom field story points
4. **Permissions**: Một số tools cần permissions đặc biệt

---

**Happy Testing!** 🚀

Nếu bạn tìm thấy bugs hoặc có suggestions, vui lòng tạo issue trên GitHub!
