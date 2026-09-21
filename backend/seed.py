"""初始化演示数据（可重复执行：已存在的账号/考试会跳过）。

创建：
- 教师 teacher / 123456
- 学生 student01 / 123456, student02 / 123456
- 一门"Demo 在线考试"（自动生成 2 页 PDF 试卷并完成页面渲染）
- 两条演示考试记录（student01 触发 Mock 高风险预警、student02 正常）
  —— 演示数据均明确标记 is_mock=True，不冒充真实 AI 结果
"""

import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Exam, ExamRecord, User, WarningRecord  # noqa: E402
from app.services import pdf_service, risk_rules  # noqa: E402
from app.services.assemblyai_service import MOCK_TRANSCRIPTS  # noqa: E402


def ensure_user(username: str, password: str, role: str) -> User:
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"  [跳过] 用户 {username} 已存在")
        return user
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"  [创建] {role}: {username} / {password}")
    return user


def ensure_demo_exam(teacher: User) -> Exam:
    exam = Exam.query.filter_by(title="Demo 在线考试（中期演示专用）").first()
    if exam:
        print(f"  [跳过] Demo 考试已存在 (id={exam.id})")
        return exam

    exam = Exam(
        title="Demo 在线考试（中期演示专用）",
        description="大学生创新创业训练计划中期检查演示考试。不设开始/结束时间，随时可进入演示。"
        "进入考试后请允许屏幕共享开始录制，提交后系统将自动进行 AI 分析。",
        status="published",
        creator_id=teacher.id,
    )
    db.session.add(exam)
    db.session.commit()

    pdf_dir = app.config["EXAM_UPLOAD_FOLDER"]
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_abs = os.path.join(pdf_dir, f"exam_demo_{exam.id}.pdf")
    page_count = pdf_service.create_demo_pdf(pdf_abs)
    pdf_service.render_pdf_pages(pdf_abs, exam.id)

    exam.pdf_path = f"exams/exam_demo_{exam.id}.pdf"
    exam.page_count = page_count
    db.session.commit()
    print(f"  [创建] Demo 考试 id={exam.id}，自动生成试卷 PDF（{page_count} 页）")
    return exam


def ensure_demo_records(exam: Exam, student01: User, student02: User) -> None:
    if ExamRecord.query.filter_by(exam_id=exam.id).count() > 0:
        print("  [跳过] Demo 考试记录已存在")
        return

    now = datetime.now()

    # 记录 1：student01 —— 预置 Mock 高风险预警（种子演示数据）
    rec1 = ExamRecord(
        exam_id=exam.id,
        student_id=student01.id,
        status="submitted",
        submit_time=now - timedelta(hours=1),
        analysis_status="completed",
        analysis_note="种子演示数据：Mock Result（演示用预置转录，非真实 AssemblyAI 返回）",
        is_mock_analysis=True,
    )
    db.session.add(rec1)
    db.session.commit()

    high = MOCK_TRANSCRIPTS[0]  # high-risk-sample
    risk = risk_rules.analyze_transcript(high["text"])
    db.session.add(
        WarningRecord(
            exam_record_id=rec1.id,
            warning_type=risk["warning_type"],
            warning_content=risk["summary"] + "（种子演示数据）",
            risk_score=risk["risk_score"],
            risk_level=risk["risk_level"],
            transcript=high["text"],
            hit_keywords=json.dumps(risk["hits"], ensure_ascii=False),
            is_mock=True,
        )
    )

    # 记录 2：student02 —— 正常作答，低风险，已录入成绩
    rec2 = ExamRecord(
        exam_id=exam.id,
        student_id=student02.id,
        status="submitted",
        submit_time=now - timedelta(hours=1),
        score=88.0,
        analysis_status="completed",
        analysis_note="种子演示数据：Mock Result（演示用预置转录，非真实 AssemblyAI 返回）",
        is_mock_analysis=True,
    )
    db.session.add(rec2)
    db.session.commit()

    clean = MOCK_TRANSCRIPTS[2]  # clean-sample
    risk2 = risk_rules.analyze_transcript(clean["text"])
    db.session.add(
        WarningRecord(
            exam_record_id=rec2.id,
            warning_type=risk2["warning_type"],
            warning_content=risk2["summary"] + "（种子演示数据）",
            risk_score=risk2["risk_score"],
            risk_level=risk2["risk_level"],
            transcript=clean["text"],
            hit_keywords=json.dumps(risk2["hits"], ensure_ascii=False),
            is_mock=True,
        )
    )
    db.session.commit()
    print("  [创建] 2 条演示考试记录（student01 高风险预警 / student02 正常，均标记 Mock）")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("== 开始写入 Demo 数据 ==")
        teacher = ensure_user("teacher", "123456", "teacher")
        student01 = ensure_user("student01", "123456", "student")
        student02 = ensure_user("student02", "123456", "student")
        exam = ensure_demo_exam(teacher)
        ensure_demo_records(exam, student01, student02)
        print("== 完成 ==")
        print("  教师账号: teacher / 123456")
        print("  学生账号: student01 / 123456, student02 / 123456")
        print(f"  Demo 考试 id={exam.id} 已发布，可随时进入演示")
