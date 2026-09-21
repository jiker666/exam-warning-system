from flask import Blueprint
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Exam, ExamRecord, WarningRecord
from ..routes.warnings import _teacher_warnings_query, _warning_summary
from ..utils.decorators import role_required
from ..utils.guards import current_user
from ..utils.response import ok

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/teacher")
@jwt_required()
@role_required("teacher")
def teacher_dashboard():
    user = current_user()
    my_exams = Exam.query.filter_by(creator_id=user.id).all()
    exam_ids = [e.id for e in my_exams]

    submitted_count = (
        ExamRecord.query.filter(ExamRecord.exam_id.in_(exam_ids), ExamRecord.status == "submitted").count()
        if exam_ids
        else 0
    )
    pending_analysis = (
        ExamRecord.query.filter(
            ExamRecord.exam_id.in_(exam_ids),
            ExamRecord.analysis_status.in_(["pending", "processing"]),
        ).count()
        if exam_ids
        else 0
    )
    warning_rows = (
        _teacher_warnings_query(user)
        .filter(WarningRecord.risk_score > 0)
        .order_by(WarningRecord.risk_score.desc(), WarningRecord.id.desc())
        .all()
    )
    recent_warnings = (
        _teacher_warnings_query(user)
        .order_by(WarningRecord.risk_score.desc(), WarningRecord.id.desc())
        .limit(5)
        .all()
    )

    return ok(
        {
            "exam_count": len(my_exams),
            "published_count": len([e for e in my_exams if e.status == "published"]),
            "record_count": submitted_count,
            "pending_analysis": pending_analysis,
            "warning_count": len(warning_rows),
            "high_risk_count": len([w for w in warning_rows if w.risk_level == "high"]),
            "recent_warnings": [_warning_summary(w) for w in recent_warnings],
        }
    )


@dashboard_bp.get("/student")
@jwt_required()
@role_required("student")
def student_dashboard():
    user = current_user()
    published = Exam.query.filter_by(status="published").all()
    available = [e for e in published if e.is_open]
    my_records = ExamRecord.query.filter_by(student_id=user.id).all()
    submitted_ids = {r.exam_id for r in my_records if r.status == "submitted"}

    return ok(
        {
            "available_count": len(available),
            "not_submitted_count": len([e for e in available if e.id not in submitted_ids]),
            "my_record_count": len(my_records),
            "submitted_count": len(submitted_ids),
            "available_exams": [e.to_dict() for e in available[:5]],
        }
    )
