from datetime import datetime

from ..extensions import db


class Exam(db.Model):
    """考试。status: draft(草稿) / published(已发布)。"""

    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)  # 可选，为空表示不限开始时间
    end_time = db.Column(db.DateTime)  # 可选，为空表示不限结束时间
    pdf_path = db.Column(db.String(512))  # 相对 uploads/ 的路径
    page_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(16), nullable=False, default="draft")
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    records = db.relationship("ExamRecord", backref="exam", lazy=True)

    @property
    def is_open(self) -> bool:
        """已发布且处于考试时间窗口内（未配置时间则视为始终开放）。"""
        if self.status != "published":
            return False
        now = datetime.now()
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True

    def to_dict(self, with_records: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M") if self.end_time else None,
            "pdf_path": self.pdf_path,
            "page_count": self.page_count or 0,
            "status": self.status,
            "is_open": self.is_open,
            "creator_id": self.creator_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        if with_records:
            data["record_count"] = len(self.records)
            data["submitted_count"] = len([r for r in self.records if r.status == "submitted"])
        return data
