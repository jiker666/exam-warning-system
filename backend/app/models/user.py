from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(db.Model):
    """系统用户：教师 / 学生。密码使用 Werkzeug 哈希存储，禁止明文。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="student")  # teacher / student
    created_at = db.Column(db.DateTime, default=datetime.now)

    exams = db.relationship("Exam", backref="creator", lazy=True)
    records = db.relationship("ExamRecord", backref="student", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
