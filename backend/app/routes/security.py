from flask import Blueprint, request
from flask_jwt_extended import verify_jwt_in_request

from ..extensions import db
from ..models import SecurityEvent
from ..utils.decorators import role_required
from ..utils.response import fail, ok

security_bp = Blueprint("security", __name__)


def _log_event(event_type: str, detail: str):
    """记录安全事件；携带有效 JWT 时附上操作者身份。"""
    user_id, username = None, None
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt, get_jwt_identity

        claims = get_jwt()
        username = claims.get("username")
        identity = get_jwt_identity()
        user_id = int(identity) if identity else None
    except Exception:  # noqa: BLE001 匿名访问也记录
        pass
    db.session.add(
        SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip=request.remote_addr,
            detail=detail,
        )
    )
    db.session.commit()


@security_bp.get("/api/admin/backup-keys")
def honeypot_endpoint():
    """蜜罐诱捕端点：正常学生与前端永远不会访问，任何访问都记录为安全事件。"""
    _log_event("honeypot_endpoint", "访问了蜜罐诱捕接口 /api/admin/backup-keys")
    return fail("禁止访问", 403, 403)


@security_bp.get("/api/security/events")
@role_required("teacher")
def list_events():
    """教师查看安全事件（蜜罐触发记录）。"""
    events = SecurityEvent.query.order_by(SecurityEvent.id.desc()).limit(50).all()
    return ok([e.to_dict() for e in events])
