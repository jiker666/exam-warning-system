from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from ..extensions import db
from ..models import User
from ..utils.guards import current_user
from ..utils.response import fail, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return fail("用户名和密码不能为空")

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return fail("用户名或密码错误", 401, 401)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "username": user.username},
    )
    return ok({"access_token": token, "user": user.to_dict()}, message="登录成功")


@auth_bp.get("/me")
@jwt_required()
def me():
    claims = get_jwt()
    user = current_user()
    if user is None:
        return fail("用户不存在", 401, 401)
    data = user.to_dict()
    data["token_claims"] = {"role": claims.get("role"), "username": claims.get("username")}
    return ok(data)
