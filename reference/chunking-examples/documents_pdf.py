"""分块示例 2 / 7 · PDF / Word / PPT

策略:文档天然按"页 / 幻灯片"分段。先把文档解析成 [(页码, 该页文本)],
      再按页切块并保留页码做出处;单页过长用固定大小+重叠兜底。

本脚本仅用标准库:load_pages() 是一个**桩(stub)**,内置样例返回每页文本,
让你能独立运行、看清切分逻辑。真实场景把 load_pages 换成:
    - PDF:  pypdf            ->  for page in reader.pages: page.extract_text()
    - Word: python-docx      ->  按段落/分页
    - PPT:  python-pptx      ->  每张幻灯片一段

直接运行:
    python documents_pdf.py
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


def fixed_size(text: str, size: int, overlap: int):
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        yield text[start : start + size]
        if start + size >= len(text):
            break


def load_pages(document_id: str) -> list[tuple[int, str]]:
    """桩:返回 [(页码, 文本)]。真实实现见模块顶部说明。"""
    return [
        (1, "检索增强生成(RAG)把模型的参数化记忆与可检索的非参数化记忆结合。"),
        (2, "离线阶段:加载、切块、嵌入、入库。在线阶段:问题嵌入、检索、拼接、生成。"
            "分块质量直接决定检索质量;块太大向量背负多主题,块太小语义被切碎。"),
        (3, "重叠用来保住跨边界的句子;经验上重叠取块大小的 10%–20%。"),
    ]


def chunk_document(document_id: str, max_chars: int = 120, overlap: int = 20):
    chunks: list[Chunk] = []
    idx = 0
    for page_no, text in load_pages(document_id):
        text = text.strip()
        if not text:
            continue
        pieces = [text] if len(text) <= max_chars else list(fixed_size(text, max_chars, overlap))
        for piece in pieces:
            chunks.append(Chunk(document_id, idx, piece, {"page": page_no}))
            idx += 1
    return chunks


def main():
    chunks = chunk_document("handbook.pdf", max_chars=60, overlap=12)
    print(f"共 {len(chunks)} 块\n")
    for c in chunks:
        print(f"[块 {c.index}] page = {c.meta['page']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
