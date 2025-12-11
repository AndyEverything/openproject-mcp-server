# Prompt Templates: Báo cáo Tuần OpenProject

> Templates để tạo báo cáo tuần từ OpenProject qua Claude MCP

## 1. Prompt Cơ bản - Sử dụng Tool Tự động

### Báo cáo tuần này
```
Tạo báo cáo tuần cho project 5 tuần này, team Backend
```

### Báo cáo tuần trước
```
Tạo báo cáo tuần cho project 3 tuần trước, team Frontend
```

### Báo cáo với khoảng thời gian cụ thể
```
Tạo báo cáo tuần cho:
- Project ID: 5
- Từ ngày: 2025-12-02
- Đến ngày: 2025-12-08
- Team: Backend Team Alpha
- Sprint goal: Complete user authentication feature
```

---

## 2. Prompt Nâng cao - Customize Báo cáo

### Lấy dữ liệu raw để tự xử lý
```
Lấy dữ liệu báo cáo tuần cho project 5 từ 2025-12-02 đến 2025-12-08 
ở dạng JSON, tôi muốn tự format
```

### Sau đó customize:
```
Từ dữ liệu trên, tạo báo cáo với:
1. Thêm section phân tích rủi ro chi tiết
2. Thêm biểu đồ phân bổ effort
3. Bỏ section Sprint Health
4. Format theo style executive summary ngắn gọn
```

---

## 3. Prompt Kết hợp - Hybrid Approach

### Bước 1: Tạo báo cáo cơ bản
```
Tạo báo cáo tuần này cho project 5
```

### Bước 2: Bổ sung thông tin
```
Bây giờ bổ sung thêm:
1. Danh sách tất cả bugs đã fix trong tuần (dùng list_work_packages)
2. Top 5 người làm nhiều nhất (dùng list_time_entries)
3. Dependencies giữa các work packages (dùng list_relations)
```

---

## 4. Templates theo Use Case

### Use Case 1: Daily Stand-up Summary
```
Tạo báo cáo ngắn cho stand-up meeting hôm nay:
- Lấy dữ liệu project 5
- Chỉ hiển thị: Done yesterday, Doing today, Blockers
- Bỏ các section khác
```

### Use Case 2: Sprint Review Report
```
Tạo báo cáo sprint review cho project 3:
- Từ ngày: 2025-11-25 (sprint start)
- Đến ngày: 2025-12-08 (sprint end)
- Tập trung vào: Deliverables, Velocity, Sprint goal achievement
- Thêm so sánh với sprint trước
```

### Use Case 3: Management Summary
```
Tạo báo cáo executive summary cho leadership:
- Chỉ hiển thị section Phụ lục (siêu gọn)
- Thêm highlights và lowlights
- Dưới 1 trang A4
```

### Use Case 4: Multi-Project Report
```
Tạo báo cáo tổng hợp cho tất cả projects:
1. Tạo báo cáo tuần này project 5
2. Tạo báo cáo tuần này project 3
3. Tạo báo cáo tuần này project 7
4. Tổng hợp highlights từ cả 3 projects
```

---

## 5. Prompts để Debug/Analyze

### Kiểm tra dữ liệu
```
Trước khi tạo báo cáo, hãy kiểm tra:
1. Project 5 có tồn tại không?
2. Có bao nhiêu work packages trong tuần này?
3. Có time entries nào không?
```

### So sánh tuần
```
So sánh 2 tuần:
1. Lấy dữ liệu tuần này (2025-12-02 đến 2025-12-08)
2. Lấy dữ liệu tuần trước (2025-11-25 đến 2025-12-01)
3. So sánh: velocity, số bugs, effort distribution
```

---

## 6. Best Practices

### ✅ Do:
- Luôn specify project ID rõ ràng
- Dùng format YYYY-MM-DD cho dates
- Với báo cáo đơn giản → dùng shortcuts (`generate_this_week_report`)
- Với customize → dùng `get_report_data` + manual processing

### ❌ Don't:
- Đừng request quá nhiều data (>200 work packages) trong 1 lần
- Đừng dùng date ranges quá dài (> 1 tháng)
- Đừng expect real-time data (có thể có delay từ OpenProject)

---

## 7. Troubleshooting Prompts

### Nếu báo cáo trống:
```
Kiểm tra xem có work packages nào updated trong khoảng thời gian này không:
- List tất cả work packages của project 5
- Filter by updated date
```

### Nếu thiếu dữ liệu:
```
Debug từng phần:
1. Test connection OpenProject
2. Get project info
3. List work packages
4. List time entries
5. Xác định phần nào bị thiếu
```

---

## Notes

- Templates này dành cho **Claude Desktop với MCP OpenProject**
- Cần configure MCP server trước khi sử dụng
- Xem full documentation tại: `docs/user_guide_vi.md`
