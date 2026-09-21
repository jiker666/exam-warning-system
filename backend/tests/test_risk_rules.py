"""risk_rules 单元测试：关键词规则与风险评分。"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.services.risk_rules import analyze_transcript, risk_level_of  # noqa: E402


def test_clean_transcript_is_low_risk():
    result = analyze_transcript("（环境音，翻卷声，长时间安静）好，这页写完了。")
    assert result["risk_score"] == 0
    assert result["risk_level"] == "low"
    assert result["warning_type"] == "none"
    assert result["hits"] == []


def test_asking_answer_keywords_score_20_each():
    result = analyze_transcript("第二题答案是什么？快点告诉我答案。")
    assert result["risk_score"] == 40  # 答案是什么(20) + 告诉我答案(20)
    assert result["risk_level"] == "medium"
    assert result["warning_type"] == "speech_keyword"
    assert {h["keyword"] for h in result["hits"]} == {"答案是什么", "告诉我答案"}


def test_case_insensitive_option_letters():
    result = analyze_transcript("第三题到底选A还是选D？")
    assert result["risk_score"] == 40
    assert result["risk_level"] == "medium"


def test_repeated_keyword_capped():
    # "答案是什么" 出现 10 次，单关键词最多累计 3 次 → 20*3 = 60（高风险）
    result = analyze_transcript("答案是什么" * 10)
    assert result["risk_score"] == 60
    assert result["risk_level"] == "high"
    hit = result["hits"][0]
    assert hit["count"] == 10 and hit["counted"] == 3


def test_score_capped_at_100():
    result = analyze_transcript("答案是什么告诉我答案选a选b这题怎么做百度一下搜一下查一下" * 3)
    assert result["risk_score"] <= 100


def test_long_keyword_not_double_counted():
    # "这题怎么做" 命中后应被替换，不应再被短词重复计分
    result = analyze_transcript("这题怎么做啊")
    assert result["risk_score"] == 20
    assert len(result["hits"]) == 1


def test_level_thresholds():
    assert risk_level_of(0) == "low"
    assert risk_level_of(29) == "low"
    assert risk_level_of(30) == "medium"
    assert risk_level_of(59) == "medium"
    assert risk_level_of(60) == "high"
    assert risk_level_of(100) == "high"


def test_empty_transcript():
    result = analyze_transcript("")
    assert result["risk_score"] == 0
    assert result["warning_type"] == "none"
