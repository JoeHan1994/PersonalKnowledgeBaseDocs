"""分块示例 5 / 7 · 图片 / 扫描件(OCR)

策略:图片本身没有文本,先 OCR 成"带版面的文本块"(每块有 bbox 坐标),
      再按版面块切;块别太小,否则全是 OCR 碎字。保留页与坐标做出处。

本脚本仅用标准库:ocr_blocks() 是一个**桩(stub)**,返回模拟的 OCR 版面块,
让你能独立运行。真实场景把它换成:
    - pytesseract.image_to_data(img, output_type=DICT)  # 含每词的 bbox
    - 或 PaddleOCR / RapidOCR(离线、对中文更友好)
然后把相邻词聚成行/段(按 y 坐标接近)即可。

直接运行:
    python image_ocr.py
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OcrBlock:
    page: int
    bbox: tuple[int, int, int, int]  # x0, y0, x1, y1
    text: str
    confidence: float


def ocr_blocks(document_id: str) -> list[OcrBlock]:
    """桩:返回模拟 OCR 版面块。真实实现见模块顶部说明。"""
    return [
        OcrBlock(1, (60, 40, 520, 80), "个人知识库构建笔记", 0.98),
        OcrBlock(1, (60, 100, 520, 180),
                 "检索增强生成把模型权重里的知识与可检索的向量索引结合起来。", 0.93),
        OcrBlock(1, (60, 200, 520, 260), "扫描件经过 OCR 后会带噪声。", 0.55),
        OcrBlock(2, (60, 40, 520, 120),
                 "分块时按版面块切,保留页码与坐标,便于跳回原图位置。", 0.91),
    ]


def chunk_ocr(document_id: str, min_conf: float = 0.6, min_chars: int = 6):
    """按 OCR 版面块切;丢弃低置信度与过短的碎块。"""
    chunks: list[Chunk] = []
    idx = 0
    for blk in ocr_blocks(document_id):
        text = blk.text.strip()
        if blk.confidence < min_conf or len(text) < min_chars:
            continue  # 低置信/太碎 -> 跳过,避免污染检索
        meta = {"page": blk.page, "bbox": blk.bbox, "confidence": round(blk.confidence, 2)}
        chunks.append(Chunk(document_id, idx, text, meta))
        idx += 1
    return chunks


def main():
    chunks = chunk_ocr("scan.pdf")
    print(f"共 {len(chunks)} 块(已过滤低置信/过短)\n")
    for c in chunks:
        print(f"[块 {c.index}] page={c.meta['page']} bbox={c.meta['bbox']} conf={c.meta['confidence']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
