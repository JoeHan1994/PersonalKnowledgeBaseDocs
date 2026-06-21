"""分块示例 1 / 7 · Markdown / 纯文本

策略:按标题层级(# ## ###)做结构切分,每块带 heading_path 出处;
      标题下正文若超过 max_chars,再退回固定大小+重叠兜底。

仅用 Python 标准库。直接运行:
    python markdown_text.py
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
    """固定大小+重叠:任何格式的兜底切法。"""
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        yield text[start : start + size]
        if start + size >= len(text):
            break


def chunk_markdown(text: str, document_id: str, max_chars: int = 200, overlap: int = 30):
    chunks: list[Chunk] = []
    path: list[str] = []
    buf: list[str] = []
    idx = 0

    def flush():
        nonlocal idx
        body = "\n".join(buf).strip()
        if not body:
            return
        heading = " > ".join(path)
        # 标题块若过长,用兜底切法再细分;否则整段一块。
        pieces = [body] if len(body) <= max_chars else list(fixed_size(body, max_chars, overlap))
        for piece in pieces:
            chunks.append(Chunk(document_id, idx, piece, {"heading_path": heading}))
            idx += 1

    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            flush()
            buf = []
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("# ").strip()
            path = path[: level - 1] + [title]
        else:
            buf.append(line)
    flush()
    return chunks


SAMPLE = """# 个人知识库
这是关于构建本地 RAG 系统的笔记。

## 分块
块是检索和引用的最小单位。块的质量决定检索的质量。

### 固定大小
按长度切,相邻块留重叠,防止句子被劈成两半谁也读不懂。

## 嵌入
把每个块映射成一个向量,语义相近的块在向量空间里也相近。
"""


def main():
    chunks = chunk_markdown(SAMPLE, document_id="notes.md", max_chars=80, overlap=15)
    print(f"共 {len(chunks)} 块\n")
    for c in chunks:
        print(f"[块 {c.index}] heading_path = {c.meta['heading_path']!r}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
