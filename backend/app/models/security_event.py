from datetime import datetime

from ..extensions import db


class SecurityEvent(db.Model):
    """安全事件（Honeypot 蜜罐触发记录等）。"""

    __tablename__ = "security_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(32), nullable=False)  # honeypot_field / honeypot_endpoint
    user_id = db.Column(db.Integer)
    username = db.Column(db.String(64))
    ip = db.Column(db.String(64))
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "username": self.username,
            "ip": self.ip,
            "detail": self.detail,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
