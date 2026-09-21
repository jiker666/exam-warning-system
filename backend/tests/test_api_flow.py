"""API 集成测试：完整主链路 + 权限 / IDOR / 蜜罐。

覆盖：登录 → 教师创建考试(上传PDF) → 发布 → 学生进入考试 → 提交(上传录像)
→ AI 分析(Mock，明确标记) → 教师查看预警 → 成绩录入 → IDOR 防护 → 蜜罐事件。
"""

import io
import time

from conftest import auth_header, login, make_user  # noqa: F401


def _make_pdf_bytes(app) -> bytes:
    from app.services import pdf_service
    import os

    path = os.path.join(app.config["EXAM_UPLOAD_FOLDER"], "test-input.pdf")
    pdf_service.create_demo_pdf(path)
    with open(path, "rb") as f:
        data = f.read()
    os.unlink(path)
    return data


def _wait_analysis(client, teacher_token, record_id, timeout=10):
    """轮询等待后台分析线程完成。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(f"/api/records/{record_id}", headers=auth_header(teacher_token))
        data = resp.get_json()["data"]
        if data["analysis_status"] in ("completed", "failed"):
            return data
        time.sleep(0.5)
    raise AssertionError("AI 分析超时未完成")


def test_full_pipeline(client, app):
    make_user("t1", "teacher")
    make_user("s1", "student")
    make_user("s2", "student")

    # ---- 登录 ----
    bad = client.post("/api/auth/login", json={"username": "t1", "password": "wrong"})
    assert bad.status_code == 401
    teacher_token = login(client, "t1")
    student_token = login(client, "s1")
    s2_token = login(client, "s2")

    # ---- 学生无权创建考试 ----
    resp = client.post(
        "/api/exams", data={"title": "x"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 403

    # ---- 教师创建考试（上传 PDF）----
    resp = client.post(
        "/api/exams",
        data={
            "title": "单元测试考试",
            "description": "pytest",
            "pdf": (io.BytesIO(_make_pdf_bytes(app)), "exam.pdf", "application/pdf"),
        },
        content_type="multipart/form-data",
        headers=auth_header(teacher_token),
    )
    assert resp.status_code == 200, resp.get_json()
    exam = resp.get_json()["data"]
    assert exam["page_count"] == 2
    assert exam["status"] == "draft"

    # 草稿对学生不可见
    resp = client.get("/api/exams", headers=auth_header(student_token))
    assert all(e["id"] != exam["id"] for e in resp.get_json()["data"])

    # ---- 发布 ----
    resp = client.post(f"/api/exams/{exam['id']}/publish", headers=auth_header(teacher_token))
    assert resp.status_code == 200

    # 学生可见，且能拿到分页试卷
    resp = client.get("/api/exams", headers=auth_header(student_token))
    assert any(e["id"] == exam["id"] for e in resp.get_json()["data"])
    resp = client.get(f"/api/exams/{exam['id']}/pages", headers=auth_header(student_token))
    assert resp.get_json()["data"]["page_count"] == 2
    resp = client.get(f"/api/exams/{exam['id']}/pages/1", headers=auth_header(student_token))
    assert resp.status_code == 200 and resp.mimetype == "image/png"

    # ---- 学生进入考试并提交录像 ----
    resp = client.post("/api/records", json={"exam_id": exam["id"]}, headers=auth_header(student_token))
    record = resp.get_json()["data"]
    assert record["status"] == "in_progress"

    fake_webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 1024  # 带 webm 魔数的模拟文件
    resp = client.post(
        f"/api/records/{record['id']}/submit",
        data={
            "recording": (io.BytesIO(fake_webm), "recording.webm", "video/webm"),
            "contact_email_backup": "",
        },
        content_type="multipart/form-data",
        headers=auth_header(student_token),
    )
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["data"]["status"] == "submitted"
    assert resp.get_json()["data"]["analysis_triggered"] is True

    # ---- 等待 AI 分析完成（Mock 模式，明确标记）----
    result = _wait_analysis(client, teacher_token, record["id"])
    assert result["analysis_status"] == "completed", result["analysis_note"]
    assert result["is_mock_analysis"] is True  # Mock 结果必须被明确标记

    # ---- 教师在预警中心看到记录 ----
    resp = client.get("/api/warnings", headers=auth_header(teacher_token))
    warnings = resp.get_json()["data"]
    assert len(warnings) >= 1
    target = [w for w in warnings if w["student_username"] == "s1"][0]
    assert target["is_mock"] is True
    assert "risk_score" in target and "hit_keywords" in target

    # 预警详情包含转录文本
    resp = client.get(f"/api/warnings/{target['id']}", headers=auth_header(teacher_token))
    detail = resp.get_json()["data"]
    assert detail["transcript"]
    assert detail["record"]["analysis_note"] and "Mock" in detail["record"]["analysis_note"]

    # ---- 教师录入成绩 ----
    resp = client.post(
        f"/api/records/{record['id']}/score",
        json={"score": 92.5},
        headers=auth_header(teacher_token),
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["score"] == 92.5

    # ---- IDOR：s2 不能访问 s1 的记录与录像 ----
    resp = client.get(f"/api/records/{record['id']}", headers=auth_header(s2_token))
    assert resp.status_code == 403
    resp = client.get(f"/api/records/{record['id']}/recording", headers=auth_header(s2_token))
    assert resp.status_code == 403
    # 学生不能访问教师预警中心
    resp = client.get("/api/warnings", headers=auth_header(student_token))
    assert resp.status_code == 403

    # ---- 蜜罐：填写隐藏字段 + 访问诱捕端点均被记录 ----
    resp = client.get("/api/admin/backup-keys")
    assert resp.status_code == 403
    resp = client.get("/api/security/events", headers=auth_header(teacher_token))
    events = resp.get_json()["data"]
    assert any(e["event_type"] == "honeypot_endpoint" for e in events)

    # ---- 未登录访问受保护接口 ----
    resp = client.get("/api/exams")
    assert resp.status_code == 401


def test_honeypot_field_logged_on_submit(client, app):
    make_user("t2", "teacher")
    make_user("s3", "student")
    teacher_token = login(client, "t2")
    student_token = login(client, "s3")

    resp = client.post(
        "/api/exams",
        data={"title": "蜜罐测试考试", "pdf": (io.BytesIO(_make_pdf_bytes(app)), "e.pdf", "application/pdf")},
        content_type="multipart/form-data",
        headers=auth_header(teacher_token),
    )
    exam_id = resp.get_json()["data"]["id"]
    client.post(f"/api/exams/{exam_id}/publish", headers=auth_header(teacher_token))

    record = client.post(
        "/api/records", json={"exam_id": exam_id}, headers=auth_header(student_token)
    ).get_json()["data"]

    resp = client.post(
        f"/api/records/{record['id']}/submit",
        data={"contact_email_backup": "bot@example.com"},  # 正常界面永不填写
        content_type="multipart/form-data",
        headers=auth_header(student_token),
    )
    assert resp.status_code == 200

    events = client.get("/api/security/events", headers=auth_header(teacher_token)).get_json()["data"]
    field_events = [e for e in events if e["event_type"] == "honeypot_field" and e["username"] == "s3"]
    assert field_events, "蜜罐字段触发未被记录"
