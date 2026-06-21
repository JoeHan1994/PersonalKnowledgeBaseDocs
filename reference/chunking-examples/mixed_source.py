"""分块示例 8 / 8 · 混合数据类型(单个来源里多种内容)

很多真实来源不是单一类型:一篇 Markdown 笔记里夹着散文、代码块、表格;
一个 Jupyter notebook 有 markdown 单元 + 代码单元;一个网页有正文 + 代码示例。

正确做法分两步(组合 / 分发式 Chunker):
  1. 切片(segment):把来源拆成"带类型的片段" [(content_type, text, meta)]
  2. 路由(dispatch):每个片段交给对应类型的切法
     - prose(散文)  -> 固定大小 + 重叠
     - code(代码)   -> AST 按函数/类(Python),其余语言按行兜底
     - table(表格)  -> 整张表一块(切碎表格会毁掉它的含义)
产物仍是统一的 Chunk,meta 里记 content_type + 出处,检索时可按类型过滤。

仅用标准库(ast、re)。直接运行:
    python mixed_source.py
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


# ---------- 各类型的切法(与单一类型脚本一致,内联以便独立运行) ----------

def split_prose(text: str, size: int, overlap: int):
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        yield text[start : start + size]
        if start + size >= len(text):
            break


def split_python(code: str):
    """按函数/类切;解析失败(非 Python 或片段不完整)则整块返回。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return [(code, None)]
    lines = code.splitlines()
    defs = [n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if not defs:
        return [(code, None)]
    return [("\n".join(lines[n.lineno - 1 : n.end_lineno]), n.name) for n in defs]


# ---------- 第 1 步:把混合 Markdown 切成带类型的片段 ----------

_FENCE = re.compile(r"^```(\w*)\s*$")


def segment_markdown(text: str):
    """产出 [(content_type, body, info)]。info 里带 heading_path / lang。"""
    segments = []
    path: list[str] = []
    buf: list[str] = []
    table_buf: list[str] = []
    in_code = False
    code_lang = ""
    code_buf: list[str] = []

    def flush_prose():
        body = "\n".join(buf).strip()
        if body:
            segments.append(("prose", body, {"heading_path": " > ".join(path)}))
        buf.clear()

    def flush_table():
        if table_buf:
            segments.append(("table", "\n".join(table_buf),
                             {"heading_path": " > ".join(path)}))
            table_buf.clear()

    for line in text.splitlines():
        fence = _FENCE.match(line.strip())
        is_table_row = line.lstrip().startswith("|") and line.rstrip().endswith("|")
        if not is_table_row:
            flush_table()  # 表格在遇到非表格行时整体收口
        if fence and not in_code:
            flush_prose()
            in_code, code_lang, code_buf = True, fence.group(1) or "text", []
            continue
        if line.strip().startswith("```") and in_code:
            segments.append(("code", "\n".join(code_buf), {"lang": code_lang}))
            in_code = False
            continue
        if in_code:
            code_buf.append(line)
        elif is_table_row:
            flush_prose()  # 表格开始前先收口散文
            table_buf.append(line.strip())
        elif line.lstrip().startswith("#"):
            flush_prose()
            level = len(line) - len(line.lstrip("#"))
            path[:] = path[: level - 1] + [line.lstrip("# ").strip()]
        else:
            buf.append(line)
    flush_table()
    flush_prose()
    return segments


# ---------- 第 2 步:路由每个片段到对应切法 ----------

def chunk_mixed(text: str, document_id: str, prose_size: int = 80, overlap: int = 15):
    chunks: list[Chunk] = []
    idx = 0
    for content_type, body, info in segment_markdown(text):
        body = body.strip()
        if not body:
            continue
        if content_type == "prose":
            for piece in split_prose(body, prose_size, overlap):
                chunks.append(Chunk(document_id, idx,
                                    piece, {"content_type": "prose", **info}))
                idx += 1
        elif content_type == "code":
            pieces = split_python(body) if info.get("lang") == "python" else [(body, None)]
            for piece, symbol in pieces:
                meta = {"content_type": "code", "lang": info.get("lang")}
                if symbol:
                    meta["symbol"] = symbol
                chunks.append(Chunk(document_id, idx, piece, meta))
                idx += 1
        elif content_type == "table":
            # 表格整块,绝不切碎
            chunks.append(Chunk(document_id, idx, body,
                                {"content_type": "table", **info}))
            idx += 1
    return chunks


SAMPLE = '''\
# 余弦相似度笔记

向量相似度衡量两个块在语义空间里有多接近。最常用的是余弦相似度,
它只看方向不看长度,因此对文本长度不敏感,非常适合检索。

```python
import math


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)
```

## 取值范围

| 相似度 | 含义 |
| 1.0 | 方向完全一致 |
| 0.0 | 正交,无关 |

下面这段散文继续解释:检索时我们对每个候选块算余弦相似度,取最高的若干块当作出处。
'''


def main():
    chunks = chunk_mixed(SAMPLE, document_id="cosine-notes.md")
    print(f"共 {len(chunks)} 块(已按 prose / code / table 分别处理)\n")
    for c in chunks:
        tag = c.meta.get("content_type")
        extra = c.meta.get("symbol") or c.meta.get("heading_path") or c.meta.get("lang") or ""
        print(f"[块 {c.index}] type={tag}  {extra}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
