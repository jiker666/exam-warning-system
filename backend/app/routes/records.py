import os
from datetime import datetime

from flask import Blueprint, current_app, request, send_file
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Exam, ExamRecord, SecurityEvent, WarningRecord
from ..services.analysis_service import start_analysis_async
from ..utils.decorators import role_required
from ..utils.files import ALLOWED_RECORDING_EXT, allowed_file, file_size_within
from ..utils.guards import can_access_record, current_user
from ..utils.response import fail, ok

records_bp = Blueprint("records", __name__, url_prefix="/api/records")

HONEYPOT_FIELD = "contact_email_backup"  # 蜜罐隐藏字段名（正常界面永远不会填写）


def _get_record_or_fail(record_id: int):
    record = db.session.get(ExamRecord, record_id)
    if record is None:
        return None, fail("考试记录不存在", 404, 404)
    return record, None


@records_bp.post("")
@jwt_required()
@role_required("student")
def start_exam():
    """学生进入考试：创建（或恢复）进行中的考试记录。"""
    user = current_user()
    data = request.get_json(silent=True) or {}
    exam_id = data.get("exam_id")
    exam = db.session.get(Exam, exam_id) if exam_id else None
    if exam is None or exam.status != "published":
        return fail("考试不存在或未发布", 404, 404)
    if not exam.is_open:
        return fail("当前不在考试开放时间内")

    record = (
        ExamRecord.query.filter_by(exam_id=exam.id, student_id=user.id)
        .order_by(ExamRecord.id.desc())
        .first()
    )
    if record is None:
        record = ExamRecord(exam_id=exam.id, student_id=user.id, status="in_progress")
        db.session.add(record)
        db.session.commit()
    return ok(record.to_dict())


@records_bp.get("")
@jwt_required()
@role_required("teacher")
def list_records():
    """教师查看自己创建的所有考试的学生记录（可按考试筛选）。"""
    user = current_user()
    query = ExamRecord.query.join(Exam, ExamRecord.exam_id == Exam.id).filter(
        Exam.creator_id == user.id
    )
    exam_id = request.args.get("exam_id", type=int)
    if exam_id:
        query = query.filter(ExamRecord.exam_id == exam_id)
    records = query.order_by(ExamRecord.id.desc()).all()
    return ok([r.to_dict() for r in records])


@records_bp.get("/mine")
@jwt_required()
@role_required("student")
def my_records():
    user = current_user()
    records = (
        ExamRecord.query.filter_by(student_id=user.id).order_by(ExamRecord.id.desc()).all()
    )
    return ok([r.to_dict() for r in records])


@records_bp.get("/<int:record_id>")
@jwt_required()
def get_record(record_id):
    user = current_user()
    record, err = _get_record_or_fail(record_id)
    if err:
        return err
    if not can_access_record(user, record):
        # IDOR 防护：不允许通过遍历 record_id 查看他人记录
        return fail("无权访问该考试记录", 403, 403)
    data = record.to_dict()
    data["warnings"] = [w.to_dict() for w in record.warnings]
    data["exam"] = record.exam.to_dict() if record.exam else None
    return ok(data)


@records_bp.post("/<int:record_id>/submit")
@jwt_required()
@role_required("student")
def submit_exam(record_id):
    """学生提交考试：可选上传屏幕录像（webm），触发 AI 分析流水线。"""
    user = current_user()
    record, err = _get_record_or_fail(record_id)
    if err:
        return err
    if record.student_id != user.id:
        return fail("无权提交他人的考试记录", 403, 403)
    if record.status == "submitted":
        return fail("该考试已提交，请勿重复提交")

    # ---- 蜜罐检测：正常界面该隐藏字段永远为空 ----
    honeypot_value = (request.form.get(HONEYPOT_FIELD) or "").strip()
    if honeypot_value:
        db.session.add(
            SecurityEvent(
                event_type="honeypot_field",
                user_id=user.id,
                username=user.username,
                ip=request.remote_addr,
                detail=f"提交考试时填写了蜜罐隐藏字段 {HONEYPOT_FIELD}={honeypot_value!r}（record_id={record.id}）",
            )
        )
        db.session.commit()

    file = request.files.get("recording")
    if file is not None and file.filename:
        if not allowed_file(file.filename, ALLOWED_RECORDING_EXT):
            return fail("录像格式仅支持 webm/mp4/mp3/wav/m4a/ogg")
        if not file_size_within(file, current_app.config["MAX_RECORDING_SIZE"]):
            return fail("录像文件过大（上限 500MB）")

        from ..utils.files import random_filename

        filename = random_filename(file.filename)
        file.save(os.path.join(current_app.config["RECORDING_UPLOAD_FOLDER"], filename))
        record.recording_path = f"recordings/{filename}"
        record.analysis_status = "pending"
        record.analysis_note = "已上传录像，等待 AI 分析"
    else:
        record.analysis_status = "failed"
        record.analysis_note = "未上传考试录像，无法进行 AI 分析"

    record.status = "submitted"
    record.submit_time = datetime.now()
    db.session.commit()

    if record.recording_path:
        start_analysis_async(record.id)

    data = record.to_dict()
    data["analysis_triggered"] = bool(record.recording_path)
    return ok(data, message="考试提交成功")


@records_bp.post("/<int:record_id>/score")
@jwt_required()
@role_required("teacher")
def set_score(record_id):
    user = current_user()
    record, err = _get_record_or_fail(record_id)
    if err:
        return err
    if record.exam is None or record.exam.creator_id != user.id:
        return fail("无权录入该记录成绩", 403, 403)

    data = request.get_json(silent=True) or {}
    try:
        score = float(data.get("score"))
    except (TypeError, ValueError):
        return fail("成绩必须为数字")
    if not 0 <= score <= 100:
        return fail("成绩需在 0 - 100 之间")

    record.score = score
    db.session.commit()
    return ok(record.to_dict(), message="成绩已保存")


@records_bp.post("/<int:record_id>/analyze")
@jwt_required()
@role_required("teacher")
def reanalyze(record_id):
    """教师手动重新触发 AI 分析。"""
    user = current_user()
    record, err = _get_record_or_fail(record_id)
    if err:
        return err
    if record.exam is None or record.exam.creator_id != user.id:
        return fail("无权操作该记录", 403, 403)
    if not record.recording_path:
        return fail("该记录没有考试录像，无法分析")

    start_analysis_async(record.id)
    return ok(record.to_dict(), message="已重新触发 AI 分析")


@records_bp.get("/<int:record_id>/recording")
@jwt_required()
def get_recording(record_id):
    """考试录像回放：仅记录所属学生本人或该考试创建教师（防 IDOR）。"""
    user = current_user()
    record, err = _get_record_or_fail(record_id)
    if err:
        return err
    if not can_access_record(user, record):
        return fail("无权访问该录像", 403, 403)
    if not record.recording_path:
        return fail("该记录没有考试录像", 404, 404)

    abs_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], os.path.basename(record.recording_path)
    )
    if not os.path.isfile(abs_path):
        return fail("录像文件不存在", 404, 404)

    ext = os.path.splitext(abs_path)[1].lower()
    mimetype = {
        ".webm": "video/webm",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }.get(ext, "application/octet-stream")
    return send_file(abs_path, mimetype=mimetype, conditional=True)
