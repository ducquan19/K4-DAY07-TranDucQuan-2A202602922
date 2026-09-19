#!/usr/bin/env python3
"""Benchmark runner for Lab 07 - Embedding & Vector Store.

Evaluates chunking strategies on the VinUni Tuition Fees corpus (data/hoc-phi)
across 5 benchmark queries defined in report/REPORT_NHOM.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

load_dotenv()

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import GeminiEmbedder, MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path("data/hoc-phi")
CACHE_FILE = Path(".embedding_cache.json")

import time

class CachedEmbedder:
    """Wrapper that caches embeddings to disk to minimize API calls and latency."""

    def __init__(self, base_embedder: any) -> None:
        self.base = base_embedder
        self.cache: dict[str, list[float]] = {}
        if CACHE_FILE.exists():
            try:
                self.cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}

    def __call__(self, text: str) -> list[float]:
        key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if key in self.cache:
            return self.cache[key]
        for attempt in range(5):
            try:
                vec = self.base(text)
                self.cache[key] = vec
                self.save()
                return vec
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
                    wait_time = 30 + attempt * 10
                    print(f"\n[Rate Limit 429] Waiting {wait_time}s before retrying...", flush=True)
                    time.sleep(wait_time)
                else:
                    raise e
        return self.base(text)

    def save(self) -> None:
        try:
            CACHE_FILE.write_text(json.dumps(self.cache), encoding="utf-8")
        except Exception:
            pass


BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Mức học phí niêm yết một năm của chương trình Cử nhân Điều dưỡng tại VinUniversity là bao nhiêu và học phí này đã bao gồm những chi phí nào?",
        "filter": None,
        "expected_doc": "hoc-phi-cu-nhan-vinuni",
        "gold_answer": "Học phí niêm yết của Cử nhân Điều dưỡng là 349.650.000 VNĐ/năm (174.825.000 VNĐ/kỳ, 9.780.000 VNĐ/tín chỉ). Mức học phí này đã bao gồm trọn gói: phí đào tạo lý thuyết và thực hành lâm sàng/thí nghiệm, phí sử dụng cơ sở vật chất và thư viện, bản quyền hệ thống CNTT hỗ trợ học tập, cùng các hoạt động sinh viên (tuần lễ định hướng, dịch vụ y tế học đường, tư vấn tâm lý, cố vấn học thuật, CLB và sự kiện văn hóa thể thao). Chưa tính khoản hỗ trợ 35% từ Tập đoàn Vingroup.",
    },
    {
        "id": 2,
        "query": "Sinh viên thanh toán học phí qua hình thức chuyển khoản ngân hàng bằng VNĐ thì cần chuyển vào số tài khoản nào, ngân hàng nào và cú pháp chuyển tiền như thế nào?",
        "filter": None,
        "expected_doc": "phuong-thuc-thanh-toan-hoc-phi-vinuni",
        "gold_answer": "Chuyển khoản VND vào số tài khoản 19034362262995 tại Ngân hàng Techcombank – Hội sở chính, tên người thụ hưởng: Cong ty TNHH Giao duc va Dao tao VinAcademy. Cú pháp chuyển tiền bắt buộc: Mã số sinh viên (Student ID) + Họ và tên sinh viên + Mô tả khoản nộp (Ví dụ: V202xxxxxx Nguyen Van A Spring 2025 Tuition and Fees).",
    },
    {
        "id": 3,
        "query": "Trường hợp sinh viên tự nguyện nộp đơn xin thôi học trong tuần lễ thêm/bớt môn học (Add/Drop week) thì được nhà trường hoàn trả bao nhiêu phần trăm học phí thực đóng?",
        "filter": None,
        "expected_doc": "quy-dinh-tai-chinh-hoan-phi-vinuni",
        "gold_answer": "Sinh viên được hoàn trả 80% học phí thực đóng nếu nộp đơn xin thôi học và được phê duyệt trước hoặc trong tuần lễ thêm/bớt môn học (Add/Drop week - 2 tuần đầu học kỳ). Nếu rút sau tuần Add/Drop đến hết tuần thứ 4 chỉ được hoàn 50%, và sau tuần thứ 4 sẽ không được hoàn trả (0%).",
    },
    {
        "id": 4,
        "query": "Để duy trì học bổng tài năng toàn phần (100% học phí) trong các năm học tiếp theo tại VinUni, sinh viên cần đáp ứng điều kiện gì về điểm GPA và kỷ luật?",
        "filter": None,
        "expected_doc": "chinh-sach-hoc-bong-tai-nang-vinuni",
        "gold_answer": "Sinh viên phải duy trì điểm trung bình tích lũy (GPA) hàng năm từ 3.2/4.0 trở lên (tính trung bình hai kỳ chính Thu và Xuân), giữ vững kỷ luật không phạm lỗi nghiêm trọng (không vi phạm kỷ luật mức Tier 3 hoặc Tier 4 theo Quy tắc Ứng xử và Liêm chính học thuật), và hoàn thành tự đánh giá E.X.C.E.L.",
    },
    {
        "id": 5,
        "query": "Chính sách cấp học bổng 100% học phí kèm sinh hoạt phí nghiên cứu hàng tháng (monthly research stipend) cho chương trình đào tạo tiến sĩ áp dụng cho đối tượng nào?",
        "filter": {"audience": "student"},
        "expected_doc": "hoc-phi-cu-nhan-vinuni",
        "gold_answer": "Với sinh viên bậc đại học (audience: student): VinUni không áp dụng học bổng nghiên cứu sinh tiến sĩ hay sinh hoạt phí hàng tháng này cho sinh viên cử nhân. Chính sách học bổng 100% học phí 4 năm đào tạo tiến sĩ kèm sinh hoạt phí nghiên cứu hàng tháng (Graduate Research Fellowship) chỉ áp dụng cho đối tượng nghiên cứu sinh tiến sĩ, giảng viên và cán bộ nghiên cứu học thuật (audience: faculty).",
    },
]


def load_corpus() -> list[tuple[dict[str, str], str, str]]:
    """Loads markdown files and extracts frontmatter metadata and body text."""
    corpus: list[tuple[dict[str, str], str, str]] = []
    for file_path in sorted(DATA_DIR.glob("*.md")):
        raw = file_path.read_text(encoding="utf-8")
        if raw.startswith("---"):
            end = raw.find("\n---\n", 3)
            if end != -1:
                fm_text = raw[3:end]
                body = raw[end + 5:].strip()
                fm = dict(re.findall(r"^(\w+):\s*(.+)$", fm_text, re.M))
                cleaned_fm = {k: v.strip().strip('"').strip("'") for k, v in fm.items()}
                corpus.append((cleaned_fm, body, file_path.stem))
                continue
        corpus.append(({"doc_id": file_path.stem}, raw, file_path.stem))
    return corpus


def run_benchmark_for_chunker(
    chunker_name: str,
    chunker_instance: any,
    embedder: any,
    corpus: list[tuple[dict[str, str], str, str]],
) -> list[dict]:
    store = EmbeddingStore(embedding_fn=embedder)
    total_chunks = 0
    docs: list[Document] = []

    for fm, body, doc_id in corpus:
        chunks = chunker_instance.chunk(body)
        total_chunks += len(chunks)
        for i, ch in enumerate(chunks):
            docs.append(
                Document(
                    id=f"{doc_id}#{i}",
                    content=ch,
                    metadata={**fm, "doc_id": doc_id, "chunk_index": i},
                )
            )

    store.add_documents(docs)

    results = []
    for q in BENCHMARK_QUERIES:
        query_text = q["query"]
        q_filter = q["filter"]
        top_matches = store.search_with_filter(query=query_text, top_k=3, metadata_filter=q_filter)
        top1 = top_matches[0] if top_matches else None

        results.append(
            {
                "query_id": q["id"],
                "query": query_text,
                "filter": q_filter,
                "top1_chunk": top1["content"][:200].replace("\n", " ") if top1 else "N/A",
                "top1_doc_id": top1["metadata"].get("doc_id", "") if top1 else "N/A",
                "score": top1["score"] if top1 else 0.0,
                "top3": [
                    {
                        "doc_id": m["metadata"].get("doc_id", ""),
                        "score": m["score"],
                        "preview": m["content"][:120].replace("\n", " "),
                    }
                    for m in top_matches
                ],
            }
        )

    return results, total_chunks, store


def main() -> int:
    corpus = load_corpus()
    print(f"Loaded {len(corpus)} documents from {DATA_DIR}")

    # Choose embedder
    if os.getenv("GEMINI_API_KEY"):
        base_embedder = GeminiEmbedder()
        print("Using GeminiEmbedder with local cache.")
    else:
        base_embedder = MockEmbedder()
        print("Using MockEmbedder.")
    embedder = CachedEmbedder(base_embedder)

    strategies = [
        ("RecursiveChunker (Trần Đức Quân)", RecursiveChunker(chunk_size=400)),
        ("SentenceChunker (Lê Đức Tùng)", SentenceChunker(max_sentences_per_chunk=3)),
    ]

    out_lines: list[str] = []
    out_lines.append("=" * 70)
    out_lines.append("KẾT QUẢ BENCHMARK RETRIEVAL — LAB 07 (K4-L3A)")
    out_lines.append(f"Chủ đề: Dịch vụ & Quy định Học phí VinUni | Tổng số tài liệu: {len(corpus)}")
    out_lines.append("=" * 70 + "\n")

    for name, chunker in strategies:
        print(f"\n--- Running benchmark for: {name} ---")
        results, total_chunks, store = run_benchmark_for_chunker(name, chunker, embedder, corpus)
        out_lines.append(f"### CHIẾN LƯỢC: {name} (Tổng số chunk: {total_chunks})")
        for res in results:
            q_id = res["query_id"]
            filter_str = f" [Filter: {res['filter']}]" if res["filter"] else ""
            out_lines.append(f"\nCâu {q_id}: {res['query']}{filter_str}")
            out_lines.append(f"  - Top-1 Doc: {res['top1_doc_id']} (Score: {res['score']:.4f})")
            out_lines.append(f"  - Top-1 Trích đoạn: {res['top1_chunk']}...")
            out_lines.append("  - Top-3 Danh sách:")
            for rank, item in enumerate(res["top3"], 1):
                out_lines.append(f"     [{rank}] {item['doc_id']} (score={item['score']:.4f}): {item['preview']}...")

        # Run A/B test for Query 5 (with vs without filter) directly on the existing store
        print(f"  A/B Test Query 5 on {name}...")
        q5 = BENCHMARK_QUERIES[4]["query"]
        with_filter = store.search_with_filter(q5, top_k=3, metadata_filter={"audience": "student"})
        without_filter = store.search_with_filter(q5, top_k=3, metadata_filter=None)

        out_lines.append(f"\n[A/B TEST QUERY 5 on {name}]")
        out_lines.append(f"  * CÓ FILTER audience=student -> Top 1 Doc: {with_filter[0]['metadata'].get('doc_id') if with_filter else 'N/A'}")
        out_lines.append(f"  * KHÔNG FILTER               -> Top 1 Doc: {without_filter[0]['metadata'].get('doc_id') if without_filter else 'N/A'}")
        out_lines.append("-" * 70)

    embedder.save()

    output_text = "\n".join(out_lines)
    Path("ket_qua_benchmark.txt").write_text(output_text, encoding="utf-8")
    print(f"\nSaved benchmark results to ket_qua_benchmark.txt")
    print("\n" + output_text[:1200] + "\n... [Xem tiếp trong ket_qua_benchmark.txt]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
