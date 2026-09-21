import json
from datetime import datetime

from ..extensions import db


class WarningRecord(db.Model):
    """AI 风险预警记录。仅作为教师复核依据，不直接判定作弊。"""

    __tablename__ = "warning_records"

    id = db.Column(db.Integer, primary_key=True)
    exam_record_id = db.Column(db.Integer, db.ForeignKey("exam_records.id"), nullable=False, index=True)
    warning_type = db.Column(db.String(64), nullable=False)  # speech_keyword / none
    warning_content = db.Column(db.Text)
    risk_score = db.Column(db.Integer, nullable=False, default=0)
    risk_level = db.Column(db.String(16), nullable=False, default="low")  # low / medium / high
    transcript = db.Column(db.Text)
    hit_keywords = db.Column(db.Text)  # JSON 字符串，兼容 MySQL / SQLite
    is_mock = db.Column(db.Boolean, default=False)  # 明确标记是否为 Demo 模拟结果
    review_note = db.Column(db.Text)
    reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self) -> dict:
        try:
            hits = json.loads(self.hit_keywords) if self.hit_keywords else []
        except (ValueError, TypeError):
            hits = []
        return {
            "id": self.id,
            "exam_record_id": self.exam_record_id,
            "warning_type": self.warning_type,
            "warning_content": self.warning_content,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "transcript": self.transcript,
            "hit_keywords": hits,
            "is_mock": bool(self.is_mock),
            "review_note": self.review_note,
            "reviewed": bool(self.reviewed),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
