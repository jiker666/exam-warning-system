"""PDF 试卷服务：保存 PDF → PyMuPDF 逐页渲染 PNG → 供前端分页展示。"""

import os

import pymupdf as fitz  # PyMuPDF
from flask import current_app


class PDFServiceError(Exception):
    pass


def render_pdf_pages(pdf_abs_path: str, exam_id: int) -> int:
    """将 PDF 逐页渲染为 PNG 保存到 uploads/exam_images/<exam_id>/，返回页数。"""
    img_dir = os.path.join(current_app.config["EXAM_IMAGE_FOLDER"], str(exam_id))
    os.makedirs(img_dir, exist_ok=True)
    # 清理旧页面图片，支持更换试卷
    for old in os.listdir(img_dir):
        if old != ".gitkeep":
            os.remove(os.path.join(img_dir, old))

    try:
        doc = fitz.open(pdf_abs_path)
        page_count = doc.page_count
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x 清晰度，适合浏览器阅读
            pix.save(os.path.join(img_dir, f"page_{i + 1}.png"))
        doc.close()
    except Exception as e:
        raise PDFServiceError(f"PDF 解析失败: {e}") from e

    if page_count == 0:
        raise PDFServiceError("PDF 文件没有任何页面")
    return page_count


def save_and_render(exam_id: int, file_storage) -> dict:
    """保存上传的 PDF 并渲染页面图片，返回 {pdf_rel_path, page_count}。"""
    from ..utils.files import random_filename

    filename = random_filename(file_storage.filename or "exam.pdf")
    pdf_dir = current_app.config["EXAM_UPLOAD_FOLDER"]
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_abs = os.path.join(pdf_dir, filename)
    file_storage.save(pdf_abs)

    try:
        page_count = render_pdf_pages(pdf_abs, exam_id)
    except PDFServiceError:
        os.unlink(pdf_abs)
        raise

    return {"pdf_rel_path": f"exams/{filename}", "page_count": page_count}


def create_demo_pdf(abs_path: str) -> int:
    """用 PyMuPDF 生成一份 2 页的演示试卷（seed 使用，无需外部文件）。"""
    doc = fitz.open()
    page1_lines = [
        ("2026 学年《计算机导论》期中测试（Demo）", 22),
        ("姓名：__________  学号：__________  班级：__________", 12),
        ("", 8),
        ("一、单项选择题（每题 5 分，共 40 分）", 14),
        ("", 8),
        ("1. 下列哪个是冯·诺依曼计算机的基本组成部分？", 12),
        ("   A. 运算器  B. 控制器  C. 存储器  D. 以上都是", 12),
        ("", 8),
        ("2. 一个字节的二进制位数是：", 12),
        ("   A. 4 位  B. 8 位  C. 16 位  D. 32 位", 12),
        ("", 8),
        ("3. HTTP 协议默认使用的端口号是：", 12),
        ("   A. 21  B. 25  C. 80  D. 443", 12),
        ("", 8),
        ("4. 下列存储器中访问速度最快的是：", 12),
        ("   A. 内存  B. 硬盘  C. 光盘  D. U 盘", 12),
    ]
    page2_lines = [
        ("二、简答题（每题 15 分，共 30 分）", 14),
        ("", 8),
        ("1. 简述操作系统在计算机系统中的作用。", 12),
        ("", 60),
        ("", 8),
        ("2. 简述编译型语言与解释型语言的区别，并各举一例。", 12),
        ("", 60),
        ("", 8),
        ("三、论述题（30 分）", 14),
        ("", 8),
        ("结合本课程所学，论述人工智能技术对软件开发流程的影响。", 12),
        ("", 100),
        ("", 8),
        ("—— 试卷结束，请检查后提交 ——", 12),
    ]
    for lines in (page1_lines, page2_lines):
        page = doc.new_page()
        y = 72
        for text, size in lines:
            if text:
                page.insert_text((72, y), text, fontname="china-s", fontsize=size)
            y += size + 10
    doc.save(abs_path)
    page_count = doc.page_count
    doc.close()
    return page_count
