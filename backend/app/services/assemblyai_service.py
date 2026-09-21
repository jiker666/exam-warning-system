"""AssemblyAI 语音转写服务（独立 Service）。

设计要点：
- 业务代码只调用 transcribe()，不感知第三方接口细节，不依赖第三方 SDK（纯 HTTP 实现）
- 真实模式：已配置 ASSEMBLYAI_API_KEY 且未开启 DEMO_MODE
- Mock 模式：未配置 Key / 开启 DEMO_MODE / 主动调用 mock —— 返回明确标记的模拟结果，
  绝不伪装成真实 AssemblyAI 返回
"""

import os
import random
import shutil
import subprocess
import tempfile
import time

import requests
from flask import current_app

ASSEMBLYAI_BASE = "https://api.assemblyai.com"
UPLOAD_URL = f"{ASSEMBLYAI_BASE}/v2/upload"
TRANSCRIPT_URL = f"{ASSEMBLYAI_BASE}/v2/transcript"

POLL_INTERVAL = 3  # 秒
POLL_TIMEOUT = 360  # 次（约 18 分钟）

# Demo 模式预置转录数据：用于本地演示与现场兜底，均为模拟内容
MOCK_TRANSCRIPTS = [
    {
        "tag": "high-risk-sample",
        "text": (
            "喂，在吗？第二题答案是什么？快点告诉我答案。"
            "这题怎么做啊，你帮我看一下，是选A还是选C？"
            "算了，我先百度一下这个名词解释……嗯，你再帮我搜一下第三题的相关资料。"
            "哦对了，最后一题选什么？把答案发我微信里。"
        ),
    },
    {
        "tag": "medium-risk-sample",
        "text": (
            "（翻动试卷声）喂，你现在写到第几题了？"
            "你帮我看下这道题的题目要求是什么意思……行吧，我自己再查一下书上的定义。"
        ),
    },
    {
        "tag": "clean-sample",
        "text": (
            "（环境音，翻卷声，较长时间安静）"
            "好，这页写完了，检查一下姓名和学号。"
            "（安静作答）"
        ),
    },
]


class AssemblyAIError(Exception):
    pass


def is_mock_mode() -> bool:
    cfg = current_app.config
    return cfg["DEMO_MODE"] or not cfg["ASSEMBLYAI_API_KEY"]


def mock_transcribe(reason: str) -> dict:
    """返回明确标记的模拟转录结果。"""
    sample = random.choice(MOCK_TRANSCRIPTS)
    return {
        "text": sample["text"],
        "source": "mock",
        "tag": sample["tag"],
        "detail": f"Mock Result（{reason}）—— 当前为 Demo 模拟分析，非真实 AssemblyAI 返回",
    }


def prepare_audio(recording_path: str):
    """录像音频准备：优先用 ffmpeg 抽音轨（减小上传体积），失败则原样上传视频文件。

    返回 (音频路径, 是否为临时文件)。
    """
    if shutil.which("ffmpeg") is None:
        return recording_path, False
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", recording_path, "-vn", "-ac", "1", "-ar", "16000", tmp.name],
            capture_output=True,
            timeout=600,
        )
        if result.returncode == 0 and os.path.getsize(tmp.name) > 0:
            return tmp.name, True
    except (subprocess.TimeoutExpired, OSError):
        pass
    os.unlink(tmp.name)
    return recording_path, False


def _transcribe_real(audio_path: str) -> dict:
    key = current_app.config["ASSEMBLYAI_API_KEY"]
    language = current_app.config["TRANSCRIPT_LANGUAGE_CODE"] or None
    headers = {"authorization": key}

    try:
        with open(audio_path, "rb") as f:
            resp = requests.post(UPLOAD_URL, headers=headers, data=f, timeout=600)
        resp.raise_for_status()
        audio_url = resp.json()["upload_url"]
    except requests.RequestException as e:
        raise AssemblyAIError(f"上传音频到 AssemblyAI 失败: {e}") from e

    payload = {"audio_url": audio_url}
    if language:
        payload["language_code"] = language

    try:
        resp = requests.post(TRANSCRIPT_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        transcript_id = resp.json()["id"]
    except requests.RequestException as e:
        raise AssemblyAIError(f"创建转录任务失败: {e}") from e

    for _ in range(POLL_TIMEOUT):
        try:
            resp = requests.get(f"{TRANSCRIPT_URL}/{transcript_id}", headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise AssemblyAIError(f"查询转录状态失败: {e}") from e

        status = data.get("status")
        if status == "completed":
            return {
                "text": data.get("text") or "",
                "source": "assemblyai",
                "detail": f"AssemblyAI 真实转录（id={transcript_id}, language={language or 'auto'}）",
            }
        if status == "error":
            raise AssemblyAIError(f"AssemblyAI 转录失败: {data.get('error', '未知错误')}")

        time.sleep(POLL_INTERVAL)

    raise AssemblyAIError("AssemblyAI 转录超时")


def transcribe(audio_path: str, force_mock: bool = False) -> dict:
    """统一入口：返回 {text, source: 'assemblyai'|'mock', detail}。"""
    if force_mock:
        return mock_transcribe("强制 Demo 模式")
    if is_mock_mode():
        reason = "DEMO_MODE 已开启" if current_app.config["DEMO_MODE"] else "未配置 ASSEMBLYAI_API_KEY"
        return mock_transcribe(reason)
    return _transcribe_real(audio_path)
