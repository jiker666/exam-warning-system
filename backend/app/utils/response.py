from flask import jsonify


def ok(data=None, message: str = "success"):
    """统一成功返回: {"code": 0, "message": ..., "data": ...}"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message: str = "error", status: int = 400, code: int = 1):
    """统一失败返回，HTTP 状态码与业务 code 同时给出。"""
    return jsonify({"code": code, "message": message, "data": None}), status
