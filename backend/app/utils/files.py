import os
import uuid
from datetime import datetime

ALLOWED_PDF_EXT = {".pdf"}
ALLOWED_RECORDING_EXT = {".webm", ".mp4", ".mp3", ".wav", ".m4a", ".ogg"}


def allowed_file(filename: str, allowed_ext) -> bool:
    _, ext = os.path.splitext(filename or "")
    return ext.lower() in allowed_ext


def random_filename(filename: str) -> str:
    """生成随机文件名，防止路径穿越与文件名冲突。"""
    _, ext = os.path.splitext(filename or "")
    return f"{uuid.uuid4().hex}{ext.lower()}"


def file_size_within(file_storage, limit: int) -> bool:
    """在保存前检查上传文件大小。"""
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    return 0 < size <= limit


def parse_dt(value: str):
    """解析前端传来的 ISO 时间（datetime-local: 2026-09-21T10:00），空返回 None。"""
    if not value or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None
