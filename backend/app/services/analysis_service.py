"""考试录像 AI 分析流水线：录像 → 音频 → 转录 → 关键词检测 → 风险评分 → 预警记录。

分析在后台线程中执行，状态机：pending → processing → completed / failed。
"""

import json
import os
import threading

from flask import current_app

from ..extensions import db
from ..models import ExamRecord, WarningRecord
from . import assemblyai_service, risk_rules


def _recording_abs_path(recording_path: str) -> str:
    """recording_path 形如 recordings/xxx.webm，转换为绝对路径（防路径穿越）。"""
    rel = os.path.basename(recording_path)
    return os.path.join(current_app.config["RECORDING_UPLOAD_FOLDER"], rel)


def run_analysis(record_id: int, force_mock: bool = False) -> None:
    """在当前应用上下文中同步执行分析（供后台线程与手动重析调用）。"""
    record = db.session.get(ExamRecord, record_id)
    if record is None:
        current_app.logger.warning("分析任务取消：记录 %s 不存在", record_id)
        return
    if not record.recording_path:
        record.analysis_status = "failed"
        record.analysis_note = "该记录没有考试录像，无法进行 AI 分析"
        db.session.commit()
        return

    record.analysis_status = "processing"
    record.analysis_note = "AI 分析中……"
    db.session.commit()

    tmp_audio = None
    try:
        recording_abs = _recording_abs_path(record.recording_path)
        if not os.path.exists(recording_abs):
            raise FileNotFoundError(f"考试录像文件不存在: {record.recording_path}")

        audio_path, is_temp = assemblyai_service.prepare_audio(recording_abs)
        if is_temp:
            tmp_audio = audio_path
        result = assemblyai_service.transcribe(audio_path, force_mock=force_mock)
        risk = risk_rules.analyze_transcript(result["text"])

        warning = WarningRecord(
            exam_record_id=record.id,
            warning_type=risk["warning_type"],
            warning_content=risk["summary"],
            risk_score=risk["risk_score"],
            risk_level=risk["risk_level"],
            transcript=result["text"],
            hit_keywords=json.dumps(risk["hits"], ensure_ascii=False),
            is_mock=result["source"] == "mock",
        )
        # 重新分析时覆盖旧的预警记录
        for old in record.warnings:
            db.session.delete(old)
        db.session.add(warning)

        record.analysis_status = "completed"
        record.is_mock_analysis = result["source"] == "mock"
        record.analysis_note = result["detail"]
        db.session.commit()
        current_app.logger.info("记录 %s 分析完成: %s", record_id, result["detail"])
    except Exception as e:  # noqa: BLE001 分析失败不影响主流程
        db.session.rollback()
        record = db.session.get(ExamRecord, record_id)
        if record:
            record.analysis_status = "failed"
            record.analysis_note = f"分析失败: {e}"[:490]
            db.session.commit()
        current_app.logger.error("记录 %s 分析失败: %s", record_id, e)
    finally:
        if tmp_audio and os.path.exists(tmp_audio):
            os.unlink(tmp_audio)


def start_analysis_async(record_id: int, force_mock: bool = False) -> None:
    """提交后异步触发分析，避免阻塞上传接口。"""
    app = current_app._get_current_object()

    def worker():
        with app.app_context():
            run_analysis(record_id, force_mock=force_mock)

    threading.Thread(target=worker, daemon=True, name=f"analysis-{record_id}").start()
