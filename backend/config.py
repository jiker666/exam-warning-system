import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/
ROOT_DIR = os.path.dirname(BASE_DIR)  # 项目根目录

# .env 加载优先级：项目根目录 > backend/
load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """集中读取 .env 配置，禁止在业务代码中硬编码密钥。"""

    # ---- Flask 基础 ----
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    PORT = int(os.getenv("FLASK_PORT", "5001"))
    DEBUG = _bool("FLASK_DEBUG")

    # ---- JWT ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRE_HOURS", "24")))

    # ---- 数据库 ----
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_recycle": 3600, "pool_pre_ping": True}

    # ---- 文件上传 ----
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    EXAM_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "exams")
    RECORDING_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "recordings")
    EXAM_IMAGE_FOLDER = os.path.join(UPLOAD_FOLDER, "exam_images")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB（考试录像较大）
    MAX_PDF_SIZE = 20 * 1024 * 1024  # 试卷 PDF 上限 20MB
    MAX_RECORDING_SIZE = 500 * 1024 * 1024

    # ---- AssemblyAI ----
    ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "").strip()
    TRANSCRIPT_LANGUAGE_CODE = os.getenv("TRANSCRIPT_LANGUAGE_CODE", "zh").strip()
    DEMO_MODE = _bool("DEMO_MODE")
