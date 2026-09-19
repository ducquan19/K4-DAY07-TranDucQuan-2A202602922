from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        retrieved = self.store.search(question, top_k=top_k)
        if not retrieved:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_items = []
        for i, chunk in enumerate(retrieved, start=1):
            source = chunk["metadata"].get("source") or chunk["metadata"].get("doc_id") or chunk.get("id", f"chunk_{i}")
            context_items.append(f"[{i}] (Nguồn: {source})\n{chunk['content']}")
        context_block = "\n\n".join(context_items)

        prompt = (
            "Bạn là một trợ lý hỏi đáp dựa trên cơ sở tri thức.\n"
            "Hãy trả lời câu hỏi dưới đây chỉ dựa trên ngữ cảnh được cung cấp. "
            "Trích dẫn nguồn tài liệu bằng cách ghi rõ số thứ tự [1], [2] tương ứng. "
            "Nếu thông tin không có trong ngữ cảnh, hãy trả lời 'Không có đủ thông tin để trả lời câu hỏi này'.\n\n"
            f"--- NGỮ CẢNH ---\n{context_block}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        return self.llm_fn(prompt)
