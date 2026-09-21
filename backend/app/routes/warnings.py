from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import and_

from ..extensions import db
from ..models import Exam, ExamRecord, WarningRecord
from ..utils.decorators import role_required
from ..utils.guards import current_user
from ..utils.response import fail, ok

warnings_bp = Blueprint("warnings", __name__, url_prefix="/api/warnings")


def _teacher_warnings_query(user):
    return (
        WarningRecord.query.join(ExamRecord, WarningRecord.exam_record_id == ExamRecord.id)
        .join(Exam, ExamRecord.exam_id == Exam.id)
        .filter(Exam.creator_id == user.id)
    )


def _warning_summary(w: WarningRecord) -> dict:
    data = w.to_dict()
    data["student_username"] = w.record.student.username if w.record.student else None
    data["student_id"] = w.record.student_id
    data["exam_id"] = w.record.exam_id
    data["exam_title"] = w.record.exam.title if w.record.exam else None
    data["record_status"] = w.record.status
    data["analysis_status"] = w.record.analysis_status
    return data


def _load_owned_warning(user, warning_id: int):
    """加载预警并校验：只有该场考试的创建教师可访问。"""
    w = db.session.get(WarningRecord, warning_id)
    if w is None or w.record is None or w.record.exam is None:
        return None, fail("预警记录不存在", 404, 404)
    if w.record.exam.creator_id != user.id:
        return None, fail("无权查看该预警", 403, 403)
    return w, None


@warnings_bp.get("")
@jwt_required()
@role_required("teacher")
def list_warnings():
    user = current_user()
    query = _teacher_warnings_query(user)

    risk_level = request.args.get("risk_level")
    if risk_level in ("low", "medium", "high"):
        query = query.filter(WarningRecord.risk_level == risk_level)
    exam_id = request.args.get("exam_id", type=int)
    if exam_id:
        query = query.filter(ExamRecord.exam_id == exam_id)

    rows = query.order_by(WarningRecord.risk_score.desc(), WarningRecord.id.desc()).all()
    return ok([_warning_summary(w) for w in rows])


@warnings_bp.get("/<int:warning_id>")
@jwt_required()
@role_required("teacher")
def warning_detail(warning_id):
    user = current_user()
    w, err = _load_owned_warning(user, warning_id)
    if err:
        return err

    data = _warning_summary(w)
    data["record"] = w.record.to_dict()
    data["exam"] = w.record.exam.to_dict()
    data["student"] = w.record.student.to_dict()
    return ok(data)


@warnings_bp.post("/<int:warning_id>/review")
@jwt_required()
@role_required("teacher")
def review_warning(warning_id):
    """教师复核意见：预警只作为复核依据，最终由教师判断。"""
    user = current_user()
    w, err = _load_owned_warning(user, warning_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    review_note = (data.get("review_note") or "").strip()
    if not review_note:
        return fail("复核意见不能为空")

    w.review_note = review_note
    w.reviewed = True
    db.session.commit()
    return ok(_warning_summary(w), message="复核意见已保存")


@warnings_bp.get("/stats")
@jwt_required()
@role_required("teacher")
def warning_stats():
    user = current_user()
    base = _teacher_warnings_query(user)
    rows = base.with_entities(WarningRecord.risk_level).all()
    levels = [r[0] for r in rows]
    return ok(
        {
            "total": len(levels),
            "low": levels.count("low"),
            "medium": levels.count("medium"),
            "high": levels.count("high"),
        }
    )
