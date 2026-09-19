# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4-L3A (Dịch vụ & Học phí Đại học)
**Thành viên:** Trần Đức Quân (MSSV: 2A202602922), Lê Đức Tùng (MSSV: 2A202603005)
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định và Dịch vụ Học phí Đại học (K4-L3A Variant)

**Tại sao nhóm chọn chủ đề này?**
> Chủ đề học phí là mảng thông tin thiết yếu trong môi trường đại học, gắn liền với quyền lợi và nghĩa vụ tài chính của người học và cán bộ. Dữ liệu học phí chứa nhiều ràng buộc định lượng quan trọng (đơn giá tín chỉ, thời hạn thanh toán, tỷ lệ miễn giảm, chế tài xử phạt) và có sự phân cấp đối tượng rõ ràng (`student` vs `faculty`), giúp đánh giá chính xác độ tin cậy của mô hình RAG và chứng minh vai trò then chốt của metadata filtering.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học phí Chương trình Cử nhân và Hỗ trợ Nhà sáng lập VinUni | https://admissions.vinuni.edu.vn/vi/hoc-phi/cu-nhan/ | 2026-09-19 / 2026-2027 | 3273 | `audience: student`, `department: admissions`, `category: tuition` |
| 2 | VinUni Undergraduate Tuition Fee Structure and Credit-Based Rules | https://admissions.vinuni.edu.vn/tuition-fee/undergraduate/ | 2026-09-19 / 2026-2027 | 3045 | `audience: student`, `department: admissions`, `category: tuition` |
| 3 | Quy định Phương thức Thanh toán Học phí và Tài khoản Ngân hàng VinUni | https://admissions.vinuni.edu.vn/tuition-fee/payment-method/ | 2026-09-19 / 2024-2025 | 2507 | `audience: student`, `department: finance`, `category: payment` |
| 4 | Biểu phí Sau đại học và Học bổng Nghiên cứu sinh VinUni dành cho Giảng viên Nghiên cứu | https://admissions.vinuni.edu.vn/tuition-fee/postgraduate/ | 2026-09-19 / 2025-2026 | 2410 | `audience: faculty`, `department: graduate-school`, `category: postgraduate` |
| 5 | Quy chế Tài chính Biểu phí, Thời hạn Nộp và Chính sách Hoàn phí VinUni | https://policy.vinuni.edu.vn/all-policies/financial-regulations-and-tariff-for-student-2/ | 2026-09-19 / VU_TS03.VN_2026 | 2564 | `audience: student`, `department: finance`, `category: regulations` |
| 6 | Chính sách Học bổng Tài năng và Tiêu chí Miễn giảm Học phí VinUni | https://admissions.vinuni.edu.vn/scholarship-and-financial-aid/undergraduate-programs/scholarships/ | 2026-09-19 / 2025-2030 | 2717 | `audience: student`, `department: financial-aid-office`, `category: scholarship` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng từ cổng chính thức VinUni (`admissions.vinuni.edu.vn`, `policy.vinuni.edu.vn`), không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] 100% URL đã được kiểm tra trực tiếp, truy cập công khai HTTP 200 không bị lỗi 404/403.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `hoc-phi-cu-nhan-vinuni` | Định danh duy nhất của tài liệu, dùng để truy vết nguồn và xóa tài liệu (`delete_document`). |
| `audience` | `str` | `student`, `faculty` | Phân tách đối tượng áp dụng quy định; cực kỳ hữu ích để pre-filter nhằm tránh nhầm lẫn giữa quy định cho sinh viên cử nhân và chính sách cho giảng viên/nghiên cứu sinh. |
| `department` | `str` | `admissions`, `finance`, `graduate-school` | Lọc theo đơn vị ban hành / chuyên trách phụ trách thủ tục. |
| `category` | `str` | `tuition`, `payment`, `regulations`, `scholarship` | Giúp phân loại nghiệp vụ chuyên sâu, thu hẹp không gian tìm kiếm vector. |
| `source_url` | `str` | `https://admissions.vinuni.edu.vn/...` | Cung cấp liên kết nguồn gốc để hệ thống RAG trích dẫn bằng chứng (Grounding & Traceability). |
| `document_version` | `str` | `2026-2027` | Xác định độ mới và tính hiệu lực của quy định. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu biểu phí VinUni:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `chinh-sach-hoc-bong-tai-nang-vinuni` | FixedSizeChunker (`fixed_size`) | 16 | 192.8 ký tự | Kém; dễ cắt đôi bảng điểm GPA hoặc cắt giữa tên học bổng. |
| `chinh-sach-hoc-bong-tai-nang-vinuni` | SentenceChunker (`by_sentences`) | 6 | 387.8 ký tự | Khá tốt; trọn vẹn câu điều kiện duy trì học bổng. |
| `chinh-sach-hoc-bong-tai-nang-vinuni` | RecursiveChunker (`recursive`) | 15 | 154.5 ký tự | Tốt; bảo toàn ranh giới các gạch đầu dòng và phân mục. |
| `hoc-phi-cu-nhan-vinuni` | FixedSizeChunker (`fixed_size`) | 20 | 195.6 ký tự | Trung bình; bảng biểu phí dễ bị cắt vụn thành nhiều mảnh. |
| `hoc-phi-cu-nhan-vinuni` | SentenceChunker (`by_sentences`) | 8 | 369.0 ký tự | Tốt với văn xuôi, nhưng bảng markdown gom thành 1 câu lớn. |
| `hoc-phi-cu-nhan-vinuni` | RecursiveChunker (`recursive`) | 20 | 146.7 ký tự | Rất tốt; giữ được cấu trúc phân cấp Điều / Khoản rõ ràng. |
| `hoc-phi-sau-dai-hoc-fellowship-vinuni` | FixedSizeChunker (`fixed_size`) | 14 | 192.9 ký tự | Kém; số tiền 932.400.000 VNĐ dễ bị tách rời khỏi tên ngành. |
| `hoc-phi-sau-dai-hoc-fellowship-vinuni` | SentenceChunker (`by_sentences`) | 5 | 408.6 ký tự | Tốt; gói gọn điều kiện học bổng tiến sĩ trọn câu. |
| `hoc-phi-sau-dai-hoc-fellowship-vinuni` | RecursiveChunker (`recursive`) | 14 | 145.3 ký tự | Tốt; phân biệt mạch lạc giữa mục MBA và mục PhD. |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Đức Quân**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=400`)
- **Mô tả & lý do chọn cho chủ đề này:** Phù hợp với văn bản quy định và biểu phí học phí vì tài liệu phân cấp rõ ràng theo các tiêu đề `#`, `##`, danh sách gạch đầu dòng `-` và các đoạn văn cách nhau bởi dấu xuống dòng kép `\n\n`. Thuật toán recursive ưu tiên ngắt ở ranh giới ngữ nghĩa lớn trước, sau đó mới hạ xuống ranh giới nhỏ hơn khi vượt quá `chunk_size`.

**Thành viên 2 — Lê Đức Tùng**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Quy định đại học thường diễn đạt mỗi chế tài, điều kiện hoặc thời hạn theo từng câu văn hoàn chỉnh (như điều kiện duy trì GPA $\ge 3.2$ hay chế tài xử phạt khi quá hạn 1 tháng). Gom 3 câu liên tiếp giúp chunk mang trọn vẹn ngữ cảnh điều kiện - hệ quả mà không bị đứt đoạn giữa chừng.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Đức Quân | RecursiveChunker (`chunk_size=400`) | 10 / 10 | Tỷ lệ nén ngữ cảnh hài hòa, không làm rách ranh giới đoạn văn; điểm tương đồng cosine rất cao (0.80 - 0.91). | Khối bảng biểu số liệu dài đôi khi bị chia tách ở các dòng giữa nếu vượt kích thước 400 ký tự. |
| Lê Đức Tùng | SentenceChunker (`max_sentences=3`) | 10 / 10 | Bảo toàn trọn vẹn các câu quy định, cực mạnh ở câu hỏi về điều kiện học bổng (GPA, kỷ luật). | Với bảng markdown (bảng học phí), bộ tách câu coi cả bảng là một khối hoặc tách theo dấu chấm số thập phân nếu regex không xử lý triệt để. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** là chiến lược tối ưu nhất cho nhóm đối với văn bản biểu phí và quy chế học vụ. Nhờ danh sách separator phân tầng (`\n\n` -> `\n` -> `. ` -> ` `), RecursiveChunker vừa giữ nguyên ranh giới phân cấp tự nhiên của văn bản (tiêu đề, đoạn văn, danh sách gạch đầu dòng), vừa có cơ chế gom cụm (merge) giúp tránh hiện tượng chunk bị xé vụn. Trong khi đó, SentenceChunker gặp khó khăn khi xử lý các bảng biểu học phí markdown (dễ gom cả bảng thành 1 chunk quá lớn hoặc cắt sai theo dấu chấm số tiền thập phân).

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Mức học phí niêm yết một năm của chương trình Cử nhân Điều dưỡng tại VinUniversity là bao nhiêu và học phí này đã bao gồm những chi phí nào? | Học phí niêm yết của Cử nhân Điều dưỡng là 349.650.000 VNĐ/năm (174.825.000 VNĐ/kỳ, 9.780.000 VNĐ/tín chỉ). Mức học phí này đã bao gồm trọn gói: phí đào tạo lý thuyết và thực hành lâm sàng/thí nghiệm, phí sử dụng cơ sở vật chất và thư viện, bản quyền hệ thống CNTT hỗ trợ học tập, cùng các hoạt động sinh viên (tuần lễ định hướng, dịch vụ y tế học đường, tư vấn tâm lý, cố vấn học thuật, CLB và sự kiện văn hóa thể thao). Chưa bao gồm khoản hỗ trợ 35% từ Tập đoàn Vingroup. | `hoc-phi-cu-nhan-vinuni.md` (Mục 1 & 2) / `undergraduate-tuition-credit-vinuni.md` |
| 2 | Sinh viên thanh toán học phí qua hình thức chuyển khoản ngân hàng bằng VNĐ thì cần chuyển vào số tài khoản nào, ngân hàng nào và cú pháp chuyển tiền như thế nào? | Chuyển khoản VND vào số tài khoản `19034362262995` tại Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank) – Hội sở chính, tên người thụ hưởng: `Cong ty TNHH Giao duc va Dao tao VinAcademy`. Cú pháp chuyển tiền bắt buộc gồm: Mã số sinh viên (Student ID) + Họ và tên sinh viên + Mô tả khoản nộp (Ví dụ: `V202xxxxxx Nguyen Van A Spring 2025 Tuition and Fees`). | `phuong-thuc-thanh-toan-hoc-phi-vinuni.md` (Mục 2a) |
| 3 | Trường hợp sinh viên tự nguyện nộp đơn xin thôi học trong tuần lễ thêm/bớt môn học (Add/Drop week) thì được nhà trường hoàn trả bao nhiêu phần trăm học phí thực đóng? | Sinh viên được hoàn trả 80% học phí thực đóng nếu nộp đơn xin thôi học và được phê duyệt trước hoặc trong tuần lễ thêm/bớt môn học (Add/Drop week - 2 tuần đầu học kỳ). Nếu rút sau tuần Add/Drop đến hết tuần thứ 4 chỉ được hoàn 50%, và sau tuần thứ 4 sẽ không được hoàn trả (0%). | `quy-dinh-tai-chinh-hoan-phi-vinuni.md` (Mục 3) |
| 4 | Để duy trì học bổng tài năng toàn phần (100% học phí) trong các năm học tiếp theo tại VinUni, sinh viên cần đáp ứng điều kiện gì về điểm GPA và kỷ luật? | Sinh viên phải duy trì điểm trung bình tích lũy (GPA) hàng năm từ 3.2/4.0 trở lên (tính trung bình hai kỳ chính Thu và Xuân), giữ vững kỷ luật không phạm lỗi nghiêm trọng (không vi phạm kỷ luật mức Tier 3 hoặc Tier 4 theo Quy tắc Ứng xử và Liêm chính học thuật), và hoàn thành tự đánh giá E.X.C.E.L định kỳ với cố vấn học thuật. | `chinh-sach-hoc-bong-tai-nang-vinuni.md` (Mục 3) |
| 5 | Chính sách cấp học bổng 100% học phí kèm sinh hoạt phí nghiên cứu hàng tháng (monthly research stipend) cho chương trình đào tạo tiến sĩ áp dụng cho đối tượng nào? [Cần lọc metadata: audience=student] | Với sinh viên bậc đại học (`audience: student`): VinUni không áp dụng học bổng nghiên cứu sinh tiến sĩ hay sinh hoạt phí hàng tháng này cho sinh viên cử nhân. Chính sách học bổng 100% học phí 4 năm đào tạo tiến sĩ kèm sinh hoạt phí nghiên cứu hàng tháng (Graduate Research Fellowship) chỉ áp dụng cho đối tượng nghiên cứu sinh tiến sĩ, giảng viên và cán bộ nghiên cứu học thuật (`audience: faculty`). | `hoc-phi-sau-dai-hoc-fellowship-vinuni.md` (Mục 3) vs `hoc-phi-cu-nhan-vinuni.md` (Minh chứng yêu cầu lọc metadata `audience: student` theo ràng buộc K4-L3A) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Mức học phí niêm yết cử nhân Điều dưỡng và quyền lợi bao gồm | RecursiveChunker (Quân) | Có (top 1) | Chunking phân cấp giữ trọn vẹn biểu phí và danh mục chi phí đào tạo đi kèm |
| 2 | Thông tin tài khoản ngân hàng Techcombank và cú pháp chuyển khoản | RecursiveChunker (Quân) | Có (top 1) | Số tài khoản và tên thụ hưởng nằm trọn vẹn trong chunk, không bị đứt đoạn |
| 3 | Tỷ lệ hoàn học phí khi thôi học trong tuần Add/Drop | RecursiveChunker (Quân) | Có (top 1) | Giữ liền mạch mốc thời gian 80% (2 tuần đầu) và 50% (tuần 3-4) |
| 4 | Điều kiện GPA và kỷ luật duy trì học bổng 100% | SentenceChunker (Tùng) | Có (top 1) | Các câu điều kiện duy trì học bổng được tách trọn vẹn theo từng câu |
| 5 | Học bổng 100% kèm sinh hoạt phí tiến sĩ [Filter: audience=student] | Metadata Filter + RecursiveChunker (Quân) | Có (top 1) | Nếu không có filter `audience=student`, hệ thống nhầm lẫn lấy chính sách của faculty/sau đại học gán cho cử nhân |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata phát huy vai trò quyết định ở **Câu hỏi số 5**. Khi sinh viên hỏi về việc nhận học bổng tiến sĩ kèm sinh hoạt phí nghiên cứu hàng tháng, nếu không áp dụng bộ lọc `metadata_filter={"audience": "student"}`, thuật toán vector search dựa trên độ tương đồng ngữ nghĩa sẽ truy xuất nhầm tài liệu `hoc-phi-sau-dai-hoc-fellowship-vinuni.md` (`audience: faculty`) vì chứa các từ khóa học bổng 100% học phí, dẫn tới câu trả lời sai lệch thực tế cho sinh viên đại học. Khi kích hoạt bộ lọc `audience: student`, hệ thống loại trừ triệt để tài liệu sau đại học dành cho giảng viên, bảo đảm câu trả lời chuẩn xác.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Sự đánh đổi giữa kích thước chunk và độ toàn vẹn ngữ nghĩa**: Chunk quá nhỏ làm đứt gãy bảng số liệu học phí; chunk quá lớn (nguyên file) làm loãng vector embedding khiến score tương đồng giảm sút.
> 2. **Sức mạnh then chốt của Metadata Pre-Filtering**: Trong bài toán quy chế trường học, các văn bản của sinh viên và giảng viên có vốn từ vựng trùng nhau rất cao (cùng chứa các từ: học phí, học bổng 100%, đào tạo, tiến sĩ...). Chỉ có lọc metadata cứng (`audience: student`) trước khi tìm kiếm mới ngăn chặn được 100% hiện tượng trả lời sai đối tượng.
> 3. **RecursiveChunker giữ ranh giới văn bản tự nhiên**: Bằng việc ưu tiên các ranh giới đoạn văn `\n\n` và danh sách mục `\n`, RecursiveChunker giúp các trích đoạn văn bản quy định luôn giữ được ngữ cảnh hoàn chỉnh.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ dữ liệu quy chế học phí VinUni, sự khác biệt giữa hai chiến lược của hai thành viên tạo ra tác động rõ nét: `RecursiveChunker` của Trần Đức Quân đạt độ ổn định và điểm cosine tương đồng cao hơn trên các văn bản có bảng biểu và cấu trúc phân cấp; trong khi `SentenceChunker` của Lê Đức Tùng rất mạnh với các câu điều kiện rời rạc nhưng gặp hạn chế khi chia cắt các bảng số liệu phức tạp.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa các bảng biểu HTML sang cấu trúc JSON hoặc Markdown chuẩn hóa ngay từ khâu tiền xử lý, đồng thời gắn thêm metadata cấp mục (sub-category như `undergraduate_aid`, `late_penalty`) để cho phép truy vấn lọc đa tầng tinh vi hơn nữa.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
