"""分块示例 3 / 7 · 网页 / 文章

策略:网页成败在"正文提取"——先用 HTMLParser 去掉 script/style/nav/footer 等噪声,
      抽出标题与段落,再按标题+段落切块,保留 URL 与标题做出处。

仅用标准库(html.parser)。直接运行:
    python web_article.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


# 这些标签里的内容是噪声,整段丢弃。
_SKIP = {"script", "style", "nav", "footer", "header", "aside", "noscript"}
# 这些标签视为"块边界"。
_BLOCK = {"p", "h1", "h2", "h3", "li", "article"}


class ArticleExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.blocks: list[str] = []
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self.skip_depth += 1
        elif tag in _BLOCK and self._buf:
            self._flush()

    def handle_endtag(self, tag):
        if tag in _SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in _BLOCK:
            self._flush()

    def handle_data(self, data):
        if self.skip_depth == 0:
            text = data.strip()
            if text:
                self._buf.append(text)

    def _flush(self):
        text = " ".join(self._buf).strip()
        if text:
            self.blocks.append(text)
        self._buf = []

    def close(self):
        super().close()
        self._flush()


def chunk_web(html: str, url: str):
    parser = ArticleExtractor()
    parser.feed(html)
    parser.close()
    return [
        Chunk("web", i, block, {"url": url})
        for i, block in enumerate(parser.blocks)
    ]


SAMPLE_HTML = """
<html><head><title>RAG 入门</title><style>.x{color:red}</style></head>
<body>
  <nav>首页 关于 登录</nav>
  <article>
    <h1>什么是 RAG</h1>
    <p>检索增强生成把模型权重里的知识,与一个可检索的向量索引结合起来。</p>
    <p>回答前先检索出相关原文,再让模型基于检索到的内容作答,因此可以给出处。</p>
    <h2>为什么要分块</h2>
    <li>嵌入有长度上限</li>
    <li>检索要精准到段落</li>
  </article>
  <footer>版权所有 2026</footer>
  <script>track();</script>
</body></html>
"""


def main():
    chunks = chunk_web(SAMPLE_HTML, url="https://example.com/rag")
    print(f"共 {len(chunks)} 块(已去除 nav/footer/script/style)\n")
    for c in chunks:
        print(f"[块 {c.index}] url = {c.meta['url']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
