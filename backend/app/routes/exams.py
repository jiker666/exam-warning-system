import os

from flask import Blueprint, current_app, request, send_file
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Exam, ExamRecord, User
from ..services import pdf_service
from ..utils.decorators import role_required
from ..utils.files import ALLOWED_PDF_EXT, allowed_file, file_size_within, parse_dt
from ..utils.guards import current_user
from ..utils.response import fail, ok

exams_bp = Blueprint("exams", __name__, url_prefix="/api/exams")


def _latest_record(exam_id: int, student_id: int):
    return (
        ExamRecord.query.filter_by(exam_id=exam_id, student_id=student_id)
        .order_by(ExamRecord.id.desc())
        .first()
    )


def _check_view_access(user: User, exam: Exam):
    """试卷访问控制：创建教师可看任意状态；学生仅能看已发布考试。"""
    if user.role == "teacher":
        return exam.creator_id == user.id, "无权访问该考试"
    return exam.status == "published", "考试不存在或未发布"


@exams_bp.get("")
@jwt_required()
def list_exams():
    user = current_user()
    if user.role == "teacher":
        exams = Exam.query.filter_by(creator_id=user.id).order_by(Exam.id.desc()).all()
        return ok([e.to_dict(with_records=True) for e in exams])

    exams = Exam.query.filter_by(status="published").order_by(Exam.id.desc()).all()
    data = []
    for e in exams:
        item = e.to_dict(with_records=True)
        record = _latest_record(e.id, user.id)
        item["my_record"] = record.to_dict() if record else None
        data.append(item)
    return ok(data)


@exams_bp.post("")
@jwt_required()
@role_required("teacher")
def create_exam():
    user = current_user()
    title = (request.form.get("title") or "").strip()
    if not title:
        return fail("考试标题不能为空")
    description = (request.form.get("description") or "").strip() or None

    start_raw, end_raw = request.form.get("start_time"), request.form.get("end_time")
    start_time, end_time = parse_dt(start_raw), parse_dt(end_raw)
    if start_raw and start_time is None:
        return fail("开始时间格式不正确")
    if end_raw and end_time is None:
        return fail("结束时间格式不正确")
    if start_time and end_time and end_time <= start_time:
        return fail("结束时间必须晚于开始时间")

    file = request.files.get("pdf")
    if file is None or not file.filename:
        return fail("请上传 PDF 试卷")
    if not allowed_file(file.filename, ALLOWED_PDF_EXT):
        return fail("仅支持 PDF 格式试卷")
    if not file_size_within(file, current_app.config["MAX_PDF_SIZE"]):
        return fail("试卷 PDF 大小需在 20MB 以内")

    exam = Exam(
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        creator_id=user.id,
        status="draft",
    )
    db.session.add(exam)
    db.session.commit()  # 先落库拿到 id，再保存并渲染 PDF

    try:
        saved = pdf_service.save_and_render(exam.id, file)
    except pdf_service.PDFServiceError as e:
        db.session.delete(exam)
        db.session.commit()
        return fail(str(e))

    exam.pdf_path = saved["pdf_rel_path"]
    exam.page_count = saved["page_count"]
    db.session.commit()
    return ok(exam.to_dict(with_records=True), message="考试创建成功")


@exams_bp.get("/<int:exam_id>")
@jwt_required()
def get_exam(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    allowed, err = _check_view_access(user, exam)
    if not allowed:
        return fail(err, 404, 404)

    data = exam.to_dict(with_records=True)
    if user.role == "student":
        record = _latest_record(exam.id, user.id)
        data["my_record"] = record.to_dict() if record else None
    return ok(data)


@exams_bp.put("/<int:exam_id>")
@jwt_required()
@role_required("teacher")
def update_exam(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    if exam.creator_id != user.id:
        return fail("无权编辑该考试", 403, 403)

    if "title" in request.form:
        title = (request.form.get("title") or "").strip()
        if not title:
            return fail("考试标题不能为空")
        exam.title = title
    if "description" in request.form:
        exam.description = (request.form.get("description") or "").strip() or None
    if "start_time" in request.form:
        exam.start_time = parse_dt(request.form.get("start_time"))
    if "end_time" in request.form:
        exam.end_time = parse_dt(request.form.get("end_time"))
    if exam.start_time and exam.end_time and exam.end_time <= exam.start_time:
        return fail("结束时间必须晚于开始时间")

    file = request.files.get("pdf")
    if file is not None and file.filename:
        if not allowed_file(file.filename, ALLOWED_PDF_EXT):
            return fail("仅支持 PDF 格式试卷")
        if not file_size_within(file, current_app.config["MAX_PDF_SIZE"]):
            return fail("试卷 PDF 大小需在 20MB 以内")
        try:
            saved = pdf_service.save_and_render(exam.id, file)
        except pdf_service.PDFServiceError as e:
            return fail(str(e))
        exam.pdf_path = saved["pdf_rel_path"]
        exam.page_count = saved["page_count"]

    db.session.commit()
    return ok(exam.to_dict(with_records=True), message="考试更新成功")


@exams_bp.post("/<int:exam_id>/publish")
@jwt_required()
@role_required("teacher")
def publish_exam(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    if exam.creator_id != user.id:
        return fail("无权操作该考试", 403, 403)
    if not exam.pdf_path:
        return fail("请先上传试卷 PDF 再发布")
    exam.status = "published"
    db.session.commit()
    return ok(exam.to_dict(with_records=True), message="考试已发布")


@exams_bp.get("/<int:exam_id>/pages")
@jwt_required()
def list_pages(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    allowed, err = _check_view_access(user, exam)
    if not allowed:
        return fail(err, 403, 403)
    pages = [
        {"page": i, "url": f"/api/exams/{exam.id}/pages/{i}"}
        for i in range(1, (exam.page_count or 0) + 1)
    ]
    return ok({"page_count": exam.page_count or 0, "pages": pages})


@exams_bp.get("/<int:exam_id>/pages/<int:page_no>")
@jwt_required()
def get_page(exam_id, page_no):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    allowed, err = _check_view_access(user, exam)
    if not allowed:
        return fail(err, 403, 403)
    if page_no < 1 or page_no > (exam.page_count or 0):
        return fail("页面不存在", 404, 404)

    img_path = os.path.join(
        current_app.config["EXAM_IMAGE_FOLDER"], str(exam.id), f"page_{page_no}.png"
    )
    if not os.path.isfile(img_path):
        return fail("试卷图片不存在", 404, 404)
    return send_file(img_path, mimetype="image/png", conditional=True)


@exams_bp.get("/<int:exam_id>/pdf")
@jwt_required()
def get_pdf(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None or not exam.pdf_path:
        return fail("试卷文件不存在", 404, 404)
    allowed, err = _check_view_access(user, exam)
    if not allowed:
        return fail(err, 403, 403)

    pdf_abs = os.path.join(
        current_app.config["UPLOAD_FOLDER"], os.path.basename(exam.pdf_path)
    )
    if not os.path.isfile(pdf_abs):
        return fail("试卷文件不存在", 404, 404)
    return send_file(
        pdf_abs,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{exam.title}.pdf",
    )


@exams_bp.get("/<int:exam_id>/records")
@jwt_required()
@role_required("teacher")
def exam_records(exam_id):
    user = current_user()
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return fail("考试不存在", 404, 404)
    if exam.creator_id != user.id:
        return fail("无权查看该考试的记录", 403, 403)
    records = ExamRecord.query.filter_by(exam_id=exam.id).order_by(ExamRecord.id.desc()).all()
    return ok([r.to_dict() for r in records])
