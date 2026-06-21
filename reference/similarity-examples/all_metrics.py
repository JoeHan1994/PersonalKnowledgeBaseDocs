"""相似度 / 距离度量大全 —— 可独立运行,仅用标准库。

运行:  python all_metrics.py

每种度量都配一个"通俗到底"的小例子 + 一句应用场景。
向量检索里最常用的是前三种(余弦 / 点积 / 欧氏),
后面几种用于关键词、标签、去重、推荐等不同场景。
"""

from __future__ import annotations

import math
from collections import Counter


# ----------------------------------------------------------------------
# 1) 余弦相似度  Cosine similarity  —— 只看方向,不看长度
#    范围 [-1, 1];1=完全同向, 0=无关, -1=相反
#    场景:语义检索的默认选择(文本长短不影响),RAG 检索块
# ----------------------------------------------------------------------
def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)


# ----------------------------------------------------------------------
# 2) 点积 / 内积  Dot product / Inner product  —— 方向 + 长度都算
#    没有上界;若向量已归一化(长度=1),点积 == 余弦
#    场景:有些嵌入模型专门为点积训练(如 OpenAI);也是"打分"的基础
# ----------------------------------------------------------------------
def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# ----------------------------------------------------------------------
# 3) 欧氏距离  Euclidean / L2 distance  —— 地图上两点的直线距离
#    范围 [0, ∞);越小越近。Chroma 的默认度量就是它
#    场景:向量检索(尤其向量已归一化时,和余弦排序等价)
# ----------------------------------------------------------------------
def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ----------------------------------------------------------------------
# 4) 曼哈顿距离  Manhattan / L1 distance  —— 城市街区"只能横竖走"的步数
#    范围 [0, ∞);对异常维度没欧氏那么敏感
#    场景:高维稀疏数据、对离群值更稳健的检索
# ----------------------------------------------------------------------
def manhattan(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


# ----------------------------------------------------------------------
# 5) 杰卡德相似度  Jaccard  —— 两个"集合"的重合度 = 交集 / 并集
#    范围 [0, 1];1=完全一样, 0=毫无交集
#    场景:标签 / 关键词 / 去重;按 metadata(标签集合)过滤或找相似条目
# ----------------------------------------------------------------------
def jaccard(set_a, set_b):
    a, b = set(set_a), set(set_b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


# ----------------------------------------------------------------------
# 6) 汉明距离  Hamming  —— 等长序列"有几个位置不一样"
#    范围 [0, 长度];越小越像
#    场景:二值/哈希指纹(SimHash/MinHash)做近似去重;比对编码、密码位差
# ----------------------------------------------------------------------
def hamming(a, b):
    if len(a) != len(b):
        raise ValueError("汉明距离要求两序列等长")
    return sum(1 for x, y in zip(a, b) if x != y)


# ----------------------------------------------------------------------
# 7) 皮尔逊相关系数  Pearson  —— "去掉各自平均分后的余弦"
#    范围 [-1, 1];衡量两组打分的"趋势"是否一致,忽略谁更严/更松
#    场景:推荐系统(两个用户口味是否同向),忽略打分基准差异
# ----------------------------------------------------------------------
def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    da = [x - ma for x in a]
    db = [y - mb for y in b]
    num = sum(x * y for x, y in zip(da, db))
    den = math.sqrt(sum(x * x for x in da)) * math.sqrt(sum(y * y for y in db))
    return num / den if den else 0.0


# ----------------------------------------------------------------------
# 8) BM25 / 词频(TF-IDF 家族)  —— 关键词字面匹配,不懂语义
#    场景:精确名词/代码符号/型号检索;常与向量检索"混合"(hybrid)互补
#    这里给一个极简 TF 余弦,演示"按词袋比相似"
# ----------------------------------------------------------------------
def bag_of_words_cosine(text_a, text_b):
    ca, cb = Counter(text_a.split()), Counter(text_b.split())
    vocab = set(ca) | set(cb)
    va = [ca[w] for w in vocab]
    vb = [cb[w] for w in vocab]
    return cosine(va, vb)


def rule(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    # —— 1~4:用同样两个"口味向量"对比,看度量差异 ——
    # 想象一个人对 [甜, 辣, 酸] 三种味道的偏好打分
    xiao_ming = [9, 2, 1]   # 爱甜、不爱辣酸
    xiao_hong = [8, 3, 1]   # 跟小明很像
    da_zhuang = [1, 9, 8]   # 重口,跟小明相反

    rule("1) 余弦相似度  cosine —— 只看方向(口味比例),不看食量")
    print(f"  小明 vs 小红 = {cosine(xiao_ming, xiao_hong):.3f}  → 接近 1,口味几乎一致")
    print(f"  小明 vs 大壮 = {cosine(xiao_ming, da_zhuang):.3f}  → 偏低,口味相反")
    print("  通俗:就算一个人饭量大一倍,只要爱吃的'比例'一样,余弦照样高。")

    rule("2) 点积  dot —— 方向一致 + 都'热情'(分高)才得高分")
    print(f"  小明 vs 小红 = {dot(xiao_ming, xiao_hong):.1f}")
    print(f"  小明 vs 大壮 = {dot(xiao_ming, da_zhuang):.1f}")
    print("  通俗:既要方向像,又要两边打分都大,数值才大;归一化后就退化成余弦。")

    rule("3) 欧氏距离  euclidean(L2) —— 地图上两点直线距离,越小越近")
    print(f"  小明 vs 小红 = {euclidean(xiao_ming, xiao_hong):.3f}  → 很小,挨得近")
    print(f"  小明 vs 大壮 = {euclidean(xiao_ming, da_zhuang):.3f}  → 很大,离得远")
    print("  通俗:把每个人当地图上一个点,谁离我直线最近就最像。Chroma 默认用它。")

    rule("4) 曼哈顿距离  manhattan(L1) —— 像在棋盘格里走,只能横竖走的步数")
    print(f"  小明 vs 小红 = {manhattan(xiao_ming, xiao_hong):.1f}")
    print(f"  小明 vs 大壮 = {manhattan(xiao_ming, da_zhuang):.1f}")
    print("  通俗:不能走斜线,把每个维度的差距相加;对个别极端维度没欧氏那么敏感。")

    # —— 5:集合重合 ——
    rule("5) 杰卡德相似度  jaccard —— 两个收藏夹的标签重合度 = 交集 / 并集")
    note_a = {"RAG", "向量库", "Chroma", "嵌入"}
    note_b = {"RAG", "向量库", "检索", "重排"}
    print(f"  笔记A 标签 = {sorted(note_a)}")
    print(f"  笔记B 标签 = {sorted(note_b)}")
    print(f"  jaccard = {jaccard(note_a, note_b):.3f}  (交集2 / 并集6)")
    print("  通俗:两个人歌单重了几首 ÷ 一共多少首;只看'有没有',不看顺序和次数。")

    # —— 6:汉明 ——
    rule("6) 汉明距离  hamming —— 等长序列有几位不一样")
    code_a = "1011001"
    code_b = "1001011"
    diff = hamming(code_a, code_b)
    print(f"  指纹A = {code_a}")
    print(f"  指纹B = {code_b}")
    print(f"  hamming = {diff}  位不同 → 越小越像")
    print("  通俗:两个二维码/哈希指纹差几位;近似去重(SimHash)就靠它判'是不是同一篇'。")

    # —— 7:皮尔逊 ——
    rule("7) 皮尔逊相关  pearson —— 两个影评人打分'趋势'是否同步(不管谁严谁松)")
    yan_ge = [9, 8, 9, 6, 7]    # 严格的影评人,整体偏低
    kuan_song = [5, 4, 5, 2, 3]  # 宽松?其实是另一套基准,但趋势一样
    print(f"  影评人甲 = {yan_ge}")
    print(f"  影评人乙 = {kuan_song}")
    print(f"  pearson = {pearson(yan_ge, kuan_song):.3f}  → 接近 1,口味高度同步")
    print(f"  对比 cosine = {cosine(yan_ge, kuan_song):.3f}  (cosine 会被'基准高低'干扰)")
    print("  通俗:甲每部都比乙多打 4 分,但'哪部更好'的排序完全一致 → 皮尔逊照样判他们像。")

    # —— 8:词袋 ——
    rule("8) 词袋余弦  bag-of-words(BM25/TF-IDF 家族的简化版)—— 关键词字面匹配")
    q = "如何 配置 Chroma 向量库"
    d1 = "配置 Chroma 向量库 的 步骤"
    d2 = "今天 天气 真好 适合 散步"
    print(f"  问题   = 「{q}」")
    print(f"  文档1  = 「{d1}」 → {bag_of_words_cosine(q, d1):.3f}  关键词重合多")
    print(f"  文档2  = 「{d2}」 → {bag_of_words_cosine(q, d2):.3f}  几乎不沾边")
    print("  通俗:像图书馆按书名里的词找书;不懂'近义',但对型号/代码符号/专有名词最稳。")
    print("  实战常把它和向量检索'混合'(hybrid):语义找意思,关键词兜底精确词。")

    rule("一句话选型")
    print("  · 文本语义检索 → 余弦 / 点积 / 欧氏(归一化后三者排序基本一致)")
    print("  · 标签 / 关键词集合 → 杰卡德")
    print("  · 哈希指纹去重 → 汉明")
    print("  · 打分推荐、消除基准差 → 皮尔逊")
    print("  · 精确名词 / 代码 / 型号 → BM25 词袋,常与向量混合")


if __name__ == "__main__":
    main()
