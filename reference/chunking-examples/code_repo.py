"""分块示例 4 / 7 · 代码仓库

策略:代码按语义单元切——一个函数 / 类就是一块,绝不把函数劈成两半。
      用 Python 内置 ast 解析语法树,保留 symbol(符号名)与行号做出处。

仅用标准库(ast)。直接运行:
    python code_repo.py
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def chunk_python(source: str, document_id: str):
    """按顶层函数/类切块;每块带 symbol 与起止行号。"""
    tree = ast.parse(source)
    lines = source.splitlines()
    chunks: list[Chunk] = []
    idx = 0
    for node in tree.body:
        if isinstance(node, _DEFS):
            body = "\n".join(lines[node.lineno - 1 : node.end_lineno])
            meta = {
                "symbol": node.name,
                "kind": type(node).__name__,
                "lines": f"{node.lineno}-{node.end_lineno}",
            }
            chunks.append(Chunk(document_id, idx, body, meta))
            idx += 1
    return chunks


SAMPLE_CODE = '''\
import math


def cosine(a, b):
    """两个向量的余弦相似度。"""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)


class VectorStore:
    def __init__(self):
        self._items = []

    def add(self, vec, text):
        self._items.append((vec, text))

    def search(self, query, k=3):
        scored = [(cosine(query, v), t) for v, t in self._items]
        scored.sort(reverse=True)
        return scored[:k]
'''


def main():
    chunks = chunk_python(SAMPLE_CODE, document_id="store.py")
    print(f"共 {len(chunks)} 块(按函数/类)\n")
    for c in chunks:
        print(f"[块 {c.index}] {c.meta['kind']} {c.meta['symbol']}  行 {c.meta['lines']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
