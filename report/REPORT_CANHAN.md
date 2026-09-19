# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Đức Quân
**Mã số sinh viên:** 2A202602922
**Nhóm:** Nhóm K4-L3A (Học phí & Dịch vụ Đại học)
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) biểu thị góc giữa hai vector embedding trong không gian đa chiều rất nhỏ, đồng nghĩa với việc hai đoạn văn bản có sự đồng nhất cao về mặt ngữ nghĩa và ý định (semantic intent), bất kể chúng có độ dài khác nhau hay sử dụng tập từ vựng khác biệt.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên có thể nộp học phí qua cổng ngân hàng trực tuyến."
- Câu B: "Người học thực hiện đóng tiền học bằng ứng dụng Internet Banking."
- Tại sao tương đồng: Hai câu sử dụng các cặp từ đồng nghĩa/cùng trường nghĩa ("sinh viên" – "người học", "nộp học phí" – "đóng tiền học", "cổng trực tuyến" – "Internet Banking"), truyền tải cùng một thông điệp hướng dẫn thanh toán.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên nộp học phí học kỳ mùa thu trước ngày 15 tháng 10."
- Câu B: "Thực đơn món ăn trưa tại căng tin ký túc xá hôm nay có súp cá hồi."
- Tại sao khác: Hai câu thuộc hai miền chủ đề hoàn toàn tách biệt (quy chế tài chính đại học vs ẩm thực/sinh hoạt), vector định hướng theo hai vùng không gian khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid phụ thuộc trực tiếp vào độ dài (độ lớn vector / magnitude) của văn bản: hai câu cùng nghĩa nhưng một câu dài và một câu ngắn sẽ có khoảng cách Euclid lớn gây sai lệch. Ngược lại, Cosine similarity chuẩn hóa độ dài vector và chỉ đo góc tạo bởi hai vector, giúp bất biến trước sự chênh lệch độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Áp dụng công thức số chunk:
> $$\text{Số chunks} = \left\lceil \frac{\text{Độ dài} - \text{overlap}}{\text{chunk\_size} - \text{overlap}} \right\rceil = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \lceil 22.11 \rceil = 23$$
> Kiểm tra lại bằng code: `len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000))` trả về đúng 23.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap = 100, số chunks = $\lceil (10000 - 100) / (500 - 100) \rceil = \lceil 9900 / 400 \rceil = 25$ chunks (tăng thêm 2 chunk). Ta chấp nhận tốn thêm dung lượng lưu trữ vector để giữ nguyên vẹn ngữ cảnh tại các ranh giới cắt, tránh tình trạng câu văn, tên riêng hoặc bảng số liệu quan trọng bị cắt đôi làm mất ý nghĩa khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy tách câu dựa trên các dấu chấm, chấm than, hỏi chấm kèm khoảng trắng hoặc xuống dòng: `(?<=[.!?])(?:\s+|\n+)`. Cú pháp lookbehind giúp giữ nguyên vẹn dấu câu kết thúc ở chunk trước thay vì bị nuốt mất. Hàm gom đúng `max_sentences_per_chunk` câu thành một chunk và xử lý các trường hợp ngoại lệ như text rỗng trả về `[]`, nhưng vẫn còn giới hạn chưa phân biệt được chữ viết tắt (`TS.`, `ThS.`) hoặc số thập phân có dấu chấm.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Triển khai thuật toán đệ quy 2 chiều theo danh sách phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nhánh đệ quy xuống sâu sẽ tiếp tục bẻ nhỏ mảnh văn bản nếu độ dài vượt `chunk_size`. Nhánh gom lên (merge) thực hiện ghép các mảnh liền kề nhỏ lại với nhau cho đến khi tiệm cận `chunk_size` để tránh sinh ra hàng loạt chunk vụn. Base case dừng khi kích thước mảnh $\le chunk\_size$ hoặc khi danh sách separator rỗng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory dưới dạng danh sách các từ điển `dict` chứa `id`, `content`, `metadata` (đảm bảo luôn có `doc_id`), và `embedding`. Khi `search`, câu truy vấn được embed thành vector, sau đó tính tích vô hướng (`_dot`) với từng vector trong store (tương đương cosine similarity do vector đã được L2 normalized), sắp xếp giảm dần theo điểm `score` và trả về danh sách `top_k` bản ghi (đã loại bỏ key vector thô để tiết kiệm bộ nhớ).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện **Pre-filtering** (lọc trước khi tìm kiếm): chỉ giữ lại các bản ghi khớp toàn bộ các cặp key-value trong `metadata_filter` rồi mới tính điểm tương đồng. Cách này đảm bảo $k$ vị trí top kết quả không bị lãng phí bởi các bản ghi không phù hợp đối tượng. Hàm `delete_document` lọc bỏ tất cả các record có `metadata["doc_id"] == doc_id` và trả về `True` nếu kích thước store giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện quy trình RAG 3 bước: (1) Truy xuất top-k chunk liên quan qua `store.search_with_filter`; (2) Dựng prompt chặt chẽ với ngữ cảnh được đánh số thứ tự `[1] [2]...` kèm nguồn `source_url` để mô hình trích dẫn chứng cứ (Source Traceability); (3) Thêm chỉ dẫn nghiêm ngặt yêu cầu LLM chỉ dựa vào tài liệu cung cấp, nếu không có dữ liệu thì thông báo không tìm thấy, ngăn ngừa hiện tượng ảo giác (hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42 (100%)

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Đo lường bằng mô hình ngữ nghĩa `GeminiEmbedder` kết hợp hàm `compute_similarity`:

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Học phí năm học 2026 của sinh viên đại học là bao nhiêu? | Mức tiền học của sinh viên khóa mới năm 2026 là bao nhiêu? | cao | 0.9136 | Đúng |
| 2 | Thời hạn nộp tiền học kỳ mùa thu kết thúc vào ngày 15 tháng 10. | Hạn chót đóng học phí kỳ 1 là ngày 15/10/2024. | cao | 0.8833 | Đúng |
| 3 | Trường hợp sinh viên rút học phần sẽ được hoàn trả 80% học phí. | Chính sách hoàn tiền khi sinh viên hủy đăng ký môn học trong tuần đầu. | cao | 0.8148 | Đúng |
| 4 | Quy định biểu phí đào tạo và phương thức chuyển khoản ngân hàng. | Thực đơn món ăn trưa tại căng tin ký túc xá hôm nay. | thấp | 0.5897 | Đúng |
| 5 | Điều kiện duy trì học bổng toàn phần yêu cầu điểm GPA tối thiểu 3.2. | Nhiệt độ ngoài trời tại Hà Nội hôm nay là 28 độ C. | thấp | 0.5192 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số ở cặp 4 và 5 tuy "thấp" tương đối nhưng vẫn đạt ngưỡng ~0.52 - 0.58 chứ không về 0. Điều này cho thấy các mô hình Dense Embedding hiện đại ánh xạ văn bản vào một không gian phân bố dày đặc, nơi các câu đều chia sẻ những thành phần ngữ pháp chung của ngôn ngữ tự nhiên. Tuy nhiên, khoảng cách phân tách giữa cặp tương đồng (0.81 - 0.91) và cặp dị biệt (0.51 - 0.58) đủ lớn để thuật toán cosine ranking phân loại chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** với chiến lược cá nhân: **`RecursiveChunker` (`chunk_size=400`)** (trích xuất từ `ket_qua_benchmark.txt`):

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Mức học phí niêm yết một năm Cử nhân Điều dưỡng tại VinUniversity và quyền lợi? | Biểu phí Cử nhân Điều dưỡng: 349.650.000 VNĐ/năm, đã bao gồm phí đào tạo, cơ sở vật chất, CNTT và hoạt động sinh viên... | 0.8055 | Có (Rất liên quan) | Học phí Điều dưỡng là 349.650.000 VNĐ/năm, bao gồm trọn gói chi phí học tập, phòng lab, y tế và CLB. |
| 2 | Chuyển khoản ngân hàng bằng VNĐ: số tài khoản, ngân hàng, cú pháp? | Chuyển khoản VND: Techcombank – Hội sở chính, STK `19034362262995`, đơn vị thụ hưởng Cong ty TNHH Giao duc va Dao tao VinAcademy, cú pháp Student ID + Họ tên + Khoản nộp... | 0.8390 | Có (Khớp 100%) | Chuyển vào Techcombank STK 19034362262995, thụ hưởng VinAcademy, kèm cú pháp Mã SV + Tên + Nội dung nộp. |
| 3 | Thôi học trong tuần Add/Drop được hoàn bao nhiêu % học phí? | Chính sách hoàn phí: Hoàn trả 80% học phí thực đóng nếu nộp đơn thôi học trong tuần lễ thêm/bớt môn học (Add/Drop week)... | 0.9141 | Có (Khớp chính xác) | Sinh viên được hoàn trả 80% học phí thực đóng khi nộp đơn rút môn trong tuần Add/Drop (2 tuần đầu). |
| 4 | Điều kiện GPA và kỷ luật duy trì học bổng tài năng toàn phần 100%? | Điều kiện duy trì hàng năm: GPA tích lũy $\ge 3.2/4.0$, không vi phạm kỷ luật mức Tier 3 hoặc Tier 4, hoàn thành bản E.X.C.E.L... | 0.8297 | Có (Đúng điều kiện) | Phải duy trì GPA tích lũy tối thiểu 3.2, hạnh kiểm tốt không phạm lỗi Tier 3/4 và tự đánh giá E.X.C.E.L. |
| 5 | Học bổng 100% kèm sinh hoạt phí hàng tháng tiến sĩ áp dụng cho ai? [Filter: audience=student] | Khoản hỗ trợ học phí duy trì suốt khóa học sinh viên cử nhân... (Đã lọc bỏ tài liệu sau đại học dành cho giảng viên). | 0.6935 | Có (Ngăn nhầm lẫn) | Đối với sinh viên cử nhân (`audience: student`), trường không áp dụng học bổng tiến sĩ hay sinh hoạt phí nghiên cứu này. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (100%)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Nhóm học được cách tiếp cận chia nhỏ theo tiêu đề (HeadingChunker) của Thành viên 3: việc giữ nguyên heading cha gắn vào từng đoạn trích nhỏ giúp giải quyết triệt để bài toán mất ngữ cảnh khi một điều khoản quy định kéo dài nhiều đoạn.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
