from flask_jwt_extended import get_jwt_identity

from ..extensions import db
from ..models import ExamRecord, User


def current_user() -> User:
    """从 JWT 中解析当前登录用户。"""
    return db.session.get(User, int(get_jwt_identity()))


def can_access_record(user: User, record: ExamRecord) -> bool:
    """考试记录访问控制（防 IDOR）：记录所属学生本人，或该考试的创建教师。"""
    if user.role == "teacher":
        return record.exam is not None and record.exam.creator_id == user.id
    return record.student_id == user.id
