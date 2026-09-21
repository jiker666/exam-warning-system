from datetime import datetime

from ..extensions import db


class ExamRecord(db.Model):
    """学生考试记录。
    status: in_progress(进行中) / submitted(已提交)
    analysis_status: pending(待分析) / processing(分析中) / completed(已完成) / failed(失败)
    """

    __tablename__ = "exam_records"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, default=datetime.now)
    submit_time = db.Column(db.DateTime)
    recording_path = db.Column(db.String(512))  # 相对 uploads/ 的路径
    score = db.Column(db.Float)  # 教师手工录入
    status = db.Column(db.String(16), nullable=False, default="in_progress")
    analysis_status = db.Column(db.String(16), nullable=False, default="pending")
    analysis_note = db.Column(db.String(500))  # 分析来源 / 失败原因说明
    is_mock_analysis = db.Column(db.Boolean, default=False)

    warnings = db.relationship("WarningRecord", backref="record", lazy=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "student_id": self.student_id,
            "student_username": self.student.username if self.student else None,
            "exam_title": self.exam.title if self.exam else None,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None,
            "submit_time": self.submit_time.strftime("%Y-%m-%d %H:%M:%S") if self.submit_time else None,
            "recording_url": f"/api/records/{self.id}/recording" if self.recording_path else None,
            "score": self.score,
            "status": self.status,
            "analysis_status": self.analysis_status,
            "analysis_note": self.analysis_note,
            "is_mock_analysis": bool(self.is_mock_analysis),
            "risk_score": max([w.risk_score for w in self.warnings], default=0),
            "risk_level": max(
                (w.risk_level for w in self.warnings),
                key=lambda lv: {"low": 0, "medium": 1, "high": 2}.get(lv, 0),
                default="low",
            ),
        }
