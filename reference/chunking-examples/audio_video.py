"""分块示例 6 / 7 · 音频 / 视频(转写)

策略:转写结果天然带时间戳与说话人。按"时间窗口"把相邻片段聚成块
      (例如每 ~30 秒一块),保留 [mm:ss] 起止时间做出处,可跳回原片段。

本脚本仅用标准库:transcribe() 是一个**桩(stub)**,返回模拟的转写片段。
真实场景把它换成离线转写:
    - faster-whisper / openai-whisper  ->  segments: [{start, end, text}]
    - 含说话人时再做 diarization(pyannote)按说话人轮次切

直接运行:
    python audio_video.py
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
class Segment:
    start: float  # 秒
    end: float
    text: str


def transcribe(document_id: str) -> list[Segment]:
    """桩:返回模拟转写片段。真实实现见模块顶部说明。"""
    return [
        Segment(0.0, 6.5, "大家好,今天聊聊本地知识库。"),
        Segment(6.5, 14.0, "RAG 的离线阶段做四件事:加载、切块、嵌入、入库。"),
        Segment(14.0, 22.0, "在线阶段把问题也嵌入,检索出最相似的块。"),
        Segment(22.0, 31.0, "然后把原文和问题拼成提示交给模型。"),
        Segment(31.0, 39.0, "这样回答就能带上原文出处。"),
        Segment(39.0, 47.0, "分块的质量直接决定检索的质量。"),
    ]


def fmt(t: float) -> str:
    m, s = divmod(int(t), 60)
    return f"{m:02d}:{s:02d}"


def chunk_transcript(document_id: str, window: float = 30.0):
    """按时间窗口聚合片段成块。"""
    chunks: list[Chunk] = []
    idx = 0
    buf: list[Segment] = []
    win_start = None
    for seg in transcribe(document_id):
        if win_start is None:
            win_start = seg.start
        buf.append(seg)
        if seg.end - win_start >= window:
            chunks.append(_emit(document_id, idx, buf))
            idx += 1
            buf, win_start = [], None
    if buf:
        chunks.append(_emit(document_id, idx, buf))
    return chunks


def _emit(document_id: str, idx: int, segs: list[Segment]) -> Chunk:
    text = " ".join(s.text for s in segs)
    meta = {"start": fmt(segs[0].start), "end": fmt(segs[-1].end)}
    return Chunk(document_id, idx, text, meta)


def main():
    chunks = chunk_transcript("talk.mp4", window=20.0)
    print(f"共 {len(chunks)} 块(每 ~20 秒一块)\n")
    for c in chunks:
        print(f"[块 {c.index}] {c.meta['start']} – {c.meta['end']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
