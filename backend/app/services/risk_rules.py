"""异常关键词规则与风险评分 —— 全项目唯一维护处，禁止散落到业务代码。

评分规则（可解释）：
- 询问答案类关键词：+20 分/次
- 可疑行为类关键词：+10 分/次
- 同一关键词最多累计 3 次，防止重复刷分
- 总分上限 100

风险等级：
- 0 - 29   low    低风险
- 30 - 59  medium 中风险
- 60 - 100 high   高风险
"""

import re

# (类别标识, 类别名称, 权重, 关键词列表)
KEYWORD_RULES = [
    (
        "asking_answer",
        "询问答案",
        20,
        [
            "答案是什么", "告诉我答案", "答案给我", "答案发我", "发我答案",
            "选什么", "选a", "选b", "选c", "选d",
            "这题怎么做", "这道题怎么做", "这题选什么", "第几题选",
            "帮我做一下", "帮我把答案", "答案抄一下", "抄一下答案", "发答案",
        ],
    ),
    (
        "suspicious_behavior",
        "可疑行为",
        10,
        [
            "第几题", "你帮我看", "帮我看下", "帮我看一下", "看一下第",
            "发给我", "微信发", "发微信", "百度一下", "搜一下",
            "搜索一下", "查一下", "小抄", "偷偷查", "拿手机搜", "翻书看",
        ],
    ),
]

MAX_RISK_SCORE = 100
MAX_HITS_PER_KEYWORD = 3

RISK_LEVEL_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}


def risk_level_of(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _extract_snippets(text: str, keywords, max_snippets: int = 5):
    """为命中的关键词截取上下文片段，供教师复核。"""
    snippets = []
    for kw in keywords:
        for m in re.finditer(re.escape(kw), text):
            start, end = max(0, m.start() - 15), min(len(text), m.end() + 15)
            snippet = text[start:end].replace("\n", " ").strip()
            snippets.append(f"…{snippet}…")
            break  # 每个关键词只取第一处上下文
        if len(snippets) >= max_snippets:
            break
    return snippets


def analyze_transcript(text: str) -> dict:
    """对转录文本做关键词规则检测与风险评分。

    匹配前统一转小写（覆盖 "选A"/"选a"），并按关键词长度倒序替换，
    避免 "帮我看一下答案" 这类长词被短词重复计分。
    """
    raw_text = text or ""
    normalized = raw_text.lower()
    hits = []
    total = 0

    if normalized:
        # 汇总全部关键词、按长度倒序逐一计数并替换占位符
        all_words = [(cat, label, weight, w) for cat, label, weight, words in KEYWORD_RULES for w in words]
        all_words.sort(key=lambda item: len(item[3]), reverse=True)
        for category, label, weight, word in all_words:
            count = normalized.count(word)
            if count <= 0:
                continue
            counted = min(count, MAX_HITS_PER_KEYWORD)
            hits.append(
                {
                    "keyword": word,
                    "count": count,
                    "counted": counted,
                    "category": category,
                    "category_label": label,
                    "weight": weight,
                    "points": weight * counted,
                }
            )
            total += weight * counted
            normalized = normalized.replace(word, "#" * len(word))

    risk_score = min(total, MAX_RISK_SCORE)
    risk_level = risk_level_of(risk_score)
    snippets = _extract_snippets(raw_text, [h["keyword"] for h in hits])

    # 分类统计
    by_category = {}
    for h in hits:
        by_category[h["category_label"]] = by_category.get(h["category_label"], 0) + h["count"]

    if hits:
        parts = "、".join(f"{label} x{cnt}" for label, cnt in by_category.items())
        summary = f"命中 {len(hits)} 个异常关键词（{parts}），累计风险分 {risk_score} 分，风险等级：{RISK_LEVEL_LABELS[risk_level]}。"
    else:
        summary = "未检测到异常关键词，累计风险分 0 分，风险等级：低风险。"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_level_label": RISK_LEVEL_LABELS[risk_level],
        "warning_type": "speech_keyword" if hits else "none",
        "hits": hits,
        "snippets": snippets,
        "summary": summary,
    }
