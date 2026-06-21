"""分块示例 7 / 7 · 聊天记录 / 邮件

策略:单条消息太短,不适合做检索单位。按"时间窗口 + 同一会话"把连续消息
      聚成一个话题块(超过 gap 分钟的停顿就断开),保留会话 id、发言人、时间。
      邮件同理:按 thread 聚合,一封长邮件再退回固定大小兜底。

仅用标准库(datetime)。直接运行:
    python chat_email.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Chunk:
    document_id: str
    index: int
    text: str
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    ts: datetime
    sender: str
    text: str


def load_messages() -> list[Message]:
    """内置样例:一段群聊。真实场景从微信/Slack 导出解析。"""
    fmt = "%Y-%m-%d %H:%M"
    raw = [
        ("2026-06-21 09:00", "Alice", "我们今天定一下知识库的分块策略吧。"),
        ("2026-06-21 09:01", "Bob", "好,我倾向固定大小加重叠先跑通。"),
        ("2026-06-21 09:02", "Alice", "重叠取多少?"),
        ("2026-06-21 09:02", "Bob", "块大小的 10% 到 20% 比较稳。"),
        # —— 中间隔了 3 小时,应当断成新块 ——
        ("2026-06-21 12:30", "Alice", "下午我们看看嵌入模型选型。"),
        ("2026-06-21 12:31", "Bob", "本地就用 mxbai-embed-large。"),
    ]
    return [Message(datetime.strptime(t, fmt), s, x) for t, s, x in raw]


def chunk_chat(document_id: str, gap_minutes: int = 30):
    """按时间窗口聚合连续消息;停顿超过 gap_minutes 就断开成新块。"""
    chunks: list[Chunk] = []
    idx = 0
    buf: list[Message] = []

    def flush():
        nonlocal idx
        if not buf:
            return
        text = "\n".join(f"{m.sender}: {m.text}" for m in buf)
        meta = {
            "conversation": document_id,
            "start": buf[0].ts.strftime("%H:%M"),
            "end": buf[-1].ts.strftime("%H:%M"),
            "speakers": sorted({m.sender for m in buf}),
        }
        chunks.append(Chunk(document_id, idx, text, meta))
        idx += 1

    prev = None
    for msg in load_messages():
        if prev is not None and (msg.ts - prev.ts).total_seconds() > gap_minutes * 60:
            flush()
            buf = []
        buf.append(msg)
        prev = msg
    flush()
    return chunks


def main():
    chunks = chunk_chat("group-chat", gap_minutes=30)
    print(f"共 {len(chunks)} 块(按 30 分钟话题窗口)\n")
    for c in chunks:
        print(f"[块 {c.index}] {c.meta['start']}–{c.meta['end']} 参与者={c.meta['speakers']}")
        print(c.text)
        print("-" * 48)


if __name__ == "__main__":
    main()
