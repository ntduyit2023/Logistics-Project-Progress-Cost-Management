# Cấu trúc Output của AI Recommendation (Insights Schema)

Khi mô hình AI nhận đầu vào (Input) là danh sách các Task và 3 Trục Ràng buộc, nó sẽ thực thi các thuật toán Tối ưu hóa (Optimization) và trả về danh sách các **Insight/Recommendation** (Đề xuất).

Mỗi Đề xuất (Recommendation) không chỉ là một câu nói suông, mà là một Object dữ liệu chứa đầy đủ thông số kỹ thuật để tính toán ROI (Return on Investment) và rủi ro.

---

## Cấu trúc của 1 Recommendation Object

### 1. Phân loại Hành động (Action Meta)
*   **`action_type`**: `CRASHING` | `FAST_TRACKING` | `RESOURCE_LEVELING` | `AGENDA_OVERRIDE` | `TASK_SPLITTING`.
*   **`target_tasks`**: Mảng ID các công việc bị tác động (VD: `["T12", "T15"]`).
*   **`human_message`**: Lời giải thích trực quan cho người dùng (VD: *"Kích hoạt làm việc Thứ 7 & Chủ Nhật cho cụm công việc Đổ móng (T12, T15) để giải quyết tình trạng trễ tiến độ."*).

### 2. Sự biến thiên Ràng buộc (Constraint Modifications)
Đây là phần lõi kỹ thuật, mô tả chính xác con số nào ở Tầng 1 hoặc Tầng 2 bị bẻ khóa:
*   **`old_duration` ➔ `new_duration`**: (Áp dụng cho Crashing). VD: 20 days ➔ 16 days.
*   **`old_dependency` ➔ `new_dependency`**: (Áp dụng cho Fast Tracking). VD: `T12_FS_T15` ➔ `T12_SS_T15_Lag_5` (Chuyển từ nối tiếp sang song song có độ trễ).
*   **`agenda_override`**: (Áp dụng cho Vượt rào Lịch trình). VD: `[1,1,1,1,1,0,0]` ➔ `[1,1,1,1,1,1,1]`.

### 3. Đánh giá Tác động & Lợi ích (Impact & ROI Analysis)
Trình bày cái giá phải trả (Trade-off) để người Quản lý Dự án quyết định có bấm "Approve" hay không:
*   **`time_saved_days`**: Số ngày dự án được cứu (Rút ngắn thời gian tổng thể). VD: `-4 ngày`.
*   **`cost_penalty_usd`**: Số tiền phát sinh do tăng ca, mua thêm vật liệu, hoặc làm cuối tuần (Cost/Unit * Overtime_Premium). VD: `+$2,500`.
*   **`roi_score`**: Điểm tối ưu kinh tế (Tính bằng Công thức: `Tiền phạt trễ tiến độ (nếu có) - Cost Penalty`).

### 4. Đánh giá Rủi ro (Risk Assessment)
Mọi sự nới lỏng ràng buộc đều tiềm ẩn rủi ro phát sinh:
*   **`float_consumed`**: Lượng Total Float bị đốt cháy. (Việc Crashing thường biến các task Non-critical thành Critical, làm mất vùng an toàn).
*   **`new_critical_paths`**: Cảnh báo nếu hành động này sinh ra một đường găng mới, làm mạng lưới trở nên mong manh hơn (`TF` tiến về 0).
*   **`peak_resource_variance`**: Đánh giá xem việc dời lịch này có đẩy biểu đồ nhân sự lên mức "báo động vàng" (Gần sát vách `Max_Availability`) hay không.

## 5. Hành động Kép (Compound Actions) & Bài toán Không gian Trạng thái (State Space)

Trong thực tế, AI có thể kết hợp nhiều loại hành động cùng lúc để tạo ra hiệu quả tối đa. Ví dụ: **Vừa làm thêm cuối tuần (Agenda Override) + Vừa nhồi thêm thợ (Crashing)** trên cùng một Task. Khi đó, `action_type` sẽ là một mảng: `["CRASHING", "AGENDA_OVERRIDE"]`.

### Sự bùng nổ Không gian Trạng thái (State Space Explosion)
Đúng như bạn lo ngại, việc kết hợp các Action sẽ tạo ra một **Không gian tìm kiếm khổng lồ (Combinatorial Explosion)**. 
Nếu dự án có $N$ tasks, mỗi task có 3 tùy chọn Crashing, 2 tùy chọn Fast Tracking và 2 tùy chọn Agenda. Độ phức tạp không gian (Space Complexity) sẽ lên tới $O((3 \times 2 \times 2)^N) = O(12^N)$. Với một dự án 1,000 tasks, máy tính siêu cấp cũng sẽ sập (Out of Memory).

### Thuật toán Cắt tỉa (Pruning & Heuristics) của AI:
Để model không bị "nặng" và chạy Real-time, AI của chúng ta không duyệt toàn bộ không gian mà sử dụng các thuật toán "Cắt tỉa":
1. **Critical Path Pruning:** AI **tuyệt đối không** xét Crashing / Fast Tracking / Agenda Override cho các task có `Total_Float > 0`. Nhờ vậy, $N$ (tổng số task) bị thu nhỏ xuống chỉ còn $K$ (số task nằm trên đường găng). Không gian bị cắt giảm 80%.
2. **Resource Float Pruning:** Thuật toán Leveling chỉ được phép chạy trên các task có `Total_Float > 0` và bị cấm đụng vào Critical Path.
3. **Graph Neural Network (GNN) Policy:** Thay vì thử ngẫu nhiên (Brute-force), GNN sẽ "nhìn" vào hình dáng đồ thị và chỉ thẳng mặt: *"Với cụm task này, tỉ lệ thành công cao nhất là kết hợp Fast Tracking + Leveling. Bỏ qua Crashing đi vì Fixed Cost quá cao"*.

---

## Ví dụ 2: Output JSON của Compound Action:
```json
{
  "insight_id": "INS-002",
  "action_type": ["CRASHING", "AGENDA_OVERRIDE"],
  "target_tasks": ["T45"],
  "human_message": "Vừa mở khóa làm cuối tuần, vừa tăng thêm 2 Thợ cho task T45.",
  "modifications": {
    "agenda_override": [1, 1, 1, 1, 1, 1, 1],
    "resource_increase": { "Handlanger": "+2" },
    "duration_change": "10 -> 6"
  },
  "impact": {
    "time_saved_days": 4,
    "cost_penalty_usd": 3500,
    "roi_score": 72.0
  }
}
```
