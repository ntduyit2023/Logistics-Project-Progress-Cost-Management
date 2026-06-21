# 🕸️ Kiến Thức Nền Tảng: Lý Thuyết Đồ Thị (Graph Theory)

Tài liệu này cung cấp các khái niệm cơ bản nhất về đồ thị được áp dụng trực tiếp vào quản lý và tối ưu hóa dự án logistics của bạn.

---

## 1. Đồ Thị Là Gì? (Graph Concept)

Đồ thị là một cấu trúc dữ liệu gồm hai thành phần chính:
*   **Đỉnh (Node / Vertex):** Đại diện cho một đối tượng (trong dự án của bạn, mỗi đỉnh là một **công việc/nhiệm vụ**).
*   **Cạnh (Edge):** Kết nối giữa hai đỉnh. Cạnh thể hiện **mối quan hệ phụ thuộc** (Ví dụ: Công việc B chỉ được làm sau khi công việc A hoàn thành).

### Đồ thị có hướng (Directed Graph):
Trong quản lý tiến độ, mối quan hệ phụ thuộc luôn đi theo một chiều (A $\rightarrow$ B). Do đó ta dùng **Đồ thị có hướng**. Mũi tên chỉ từ công việc tiên quyết đến công việc kế cận.

---

## 2. Đồ Thị DAG (Directed Acyclic Graph) là gì?

Đây là khái niệm quan trọng nhất trong đề tài của bạn. 
*   **DAG** là đồ thị có hướng và **không có chu trình** (không có vòng lặp khép kín).

```
Hợp lệ (DAG):        Không hợp lệ (Chứa chu trình - Cycle):
  A ──> B ──> C        A ──> B ──> C
  └───> D ──>┘         ^           │
                       └───────────┘ (Vòng lặp vô hạn!)
```

*   **Tại sao dự án phải là DAG?** Vì một dự án không được phép tồn tại vòng lặp phụ thuộc (Ví dụ: A cần B xong mới làm, B lại cần A xong mới làm $\rightarrow$ dự án sẽ bị đóng băng vĩnh viễn - Deadlock).

---

## 3. Biểu Diễn Đồ Thị Trong Code Python

Để máy tính hiểu được đồ thị, ta biểu diễn nó bằng cấu trúc dữ liệu. Cách phổ biến nhất là **Danh sách kề (Adjacency List)** sử dụng Python Dictionary.

```python
# Biểu diễn đồ thị có hướng: A -> B, A -> C, B -> D, C -> D
graph = {
    'A': ['B', 'C'], # Nút A nối đến B và C
    'B': ['D'],      # Nút B nối đến D
    'C': ['D'],      # Nút C nối đến D
    'D': []          # Nút D không nối đi đâu (nút kết thúc)
}
```

---

## 4. Các Thuật Toán Đồ Thị Quan Trọng Trong Dự Án

### A. Sắp xếp Topo (Topological Sort)
*   **Mục đích:** Xếp thứ tự các công việc thành một hàng dọc sao cho các công việc tiên quyết luôn đứng trước công việc kế cận.
*   **Ví dụ:** Nếu đồ thị có $A \rightarrow B$, kết quả sắp xếp topo bắt buộc phải là $[A, B]$ chứ không thể là $[B, A]$.
*   **Cách hoạt động:** Duyệt qua đồ thị bằng thuật toán DFS (Duyệt theo chiều sâu) và đẩy các nút vào danh sách sau khi đã duyệt hết các nút con của nó.

### B. Tìm đường đi dài nhất (Longest Path in DAG) - Thuật toán Đường Găng (CPM)
Thông thường, tìm đường đi ngắn nhất (Shortest Path) rất phổ biến (như Google Maps). Nhưng trong quản lý dự án, ta cần tìm **Đường đi dài nhất**.
*   **Tại sao?** Vì tổng thời gian dự án được quyết định bởi nhánh công việc tốn nhiều thời gian nhất. Nhánh dài nhất này gọi là **Đường găng (Critical Path)**.
*   Bất kỳ sự chậm trễ nào trên các công việc thuộc đường găng sẽ trực tiếp làm trễ tiến độ toàn bộ dự án.

```
Nhánh 1: Start ──(4 ngày)──> A ──(6 ngày)──> End   => Tổng: 10 ngày
Nhánh 2: Start ──(7 ngày)──> B ──(12 ngày)──> End  => Tổng: 19 ngày (Đường găng!)
```
*Thời gian hoàn thành dự án tối thiểu phải là 19 ngày (theo nhánh dài nhất).*

---

## 📚 5. Tài Liệu Tham Khảo Nền Tảng (Foundational References)

Để trích dẫn vào đồ án hoặc tìm đọc thêm kiến thức nền tảng chính thống về đồ thị, bạn có thể tham khảo các tài liệu sau:

1.  **Sách giáo trình Đồ thị kinh điển (Open Access):**
    *   *J.A. Bondy & U.S.R. Murty (1976)*. **"Graph Theory with Applications"**. 
    *   *Ý nghĩa:* Đây là cuốn sách gối đầu giường về lý thuyết đồ thị trên toàn thế giới, bao gồm các định nghĩa toán học cơ bản và các bài toán luồng trên mạng (network flows).
    *   *Link đọc miễn phí:* [Graph Theory with Applications](https://www.freecomputerbooks.com/Graph-Theory-with-Applications.html)
2.  **Sách Đồ thị nâng cao:**
    *   *Reinhard Diestel (2017)*. **"Graph Theory"** (Graduate Texts in Mathematics, Springer).
    *   *Ý nghĩa:* Giáo trình chuẩn mực cho các lớp cao học và nghiên cứu sinh, trình bày các bài toán chứng minh và cấu trúc đồ thị phức tạp một cách cực kỳ chặt chẽ.
    *   *Link bản điện tử tác giả cung cấp miễn phí:* [Diestel Graph Theory](https://diestel-graph-theory.com/)
3.  **Giáo trình nhập môn đơn giản:**
    *   *Brian Heinold*. **"A Simple Introduction to Graph Theory"**.
    *   *Ý nghĩa:* Tài liệu cực kỳ phù hợp cho người bắt đầu từ số 0, tập trung giải thích các thuật toán như tìm chu trình, tô màu đồ thị, và duyệt cây theo cách trực quan, ít công thức toán học nặng.
    *   *Link đọc miễn phí:* [Brian Heinold Graph Theory](https://brianheinold.net/)
