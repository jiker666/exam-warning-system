import os

from flask import Flask
from werkzeug.exceptions import HTTPException

from .extensions import cors, db, jwt
from .utils.response import fail


def _ensure_upload_dirs(app: Flask) -> None:
    """启动时确保上传目录存在，并写入 .gitkeep 防止目录丢失。"""
    for key in ("EXAM_UPLOAD_FOLDER", "RECORDING_UPLOAD_FOLDER", "EXAM_IMAGE_FOLDER"):
        folder = app.config[key]
        os.makedirs(folder, exist_ok=True)
        keep = os.path.join(folder, ".gitkeep")
        if not os.path.exists(keep):
            with open(keep, "w") as f:
                f.write("")


def _register_jwt_handlers(app: Flask) -> None:
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return fail("登录已过期，请重新登录", 401, 401)

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return fail("未登录或缺少访问令牌", 401, 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return fail("访问令牌无效，请重新登录", 401, 401)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(e: HTTPException):
        return fail(e.description or e.name, e.code or 500, e.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e: Exception):
        import traceback

        app.logger.error("未处理异常: %s\n%s", e, traceback.format_exc())
        msg = f"服务器内部错误: {e}" if app.debug else "服务器内部错误，请稍后重试"
        return fail(msg, 500, 500)


def create_app(config_class: str = "config.Config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.ensure_ascii = False  # 中文直接输出，便于前端与调试

    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)

    _ensure_upload_dirs(app)
    _register_jwt_handlers(app)
    _register_error_handlers(app)

    from .routes import register_blueprints

    register_blueprints(app)

    from .utils.response import ok

    @app.route("/api/health")
    def health():
        return ok(
            {
                "status": "up",
                "demo_mode": app.config["DEMO_MODE"],
                "assemblyai_configured": bool(app.config["ASSEMBLYAI_API_KEY"]),
            }
        )

    with app.app_context():
        from . import models  # noqa: F401 确保模型已注册

        db.create_all()

    return app
