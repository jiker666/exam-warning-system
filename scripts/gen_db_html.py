"""生成数据库截图页面：查询真实 MySQL 数据渲染为 HTML（截图用）。"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

import pymysql  # noqa: E402

conn = pymysql.connect(host="localhost", user="root", database="exam_warning", charset="utf8mb4")
cur = conn.cursor()

sections = []


def q(title, sql):
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    sections.append((title, cols, rows))


cur.execute("SELECT VERSION()")
ver = cur.fetchone()[0]
cur.execute("SELECT DATABASE()")
db = cur.fetchone()[0]

q("SHOW TABLES", "SHOW TABLES")
q("users（用户表）", "SELECT id, username, role, created_at FROM users")
q("exams（考试表）", "SELECT id, title, status, page_count, pdf_path, creator_id FROM exams")
q(
    "exam_records（考试记录表）",
    "SELECT id, exam_id, student_id, status, analysis_status, is_mock_analysis, score FROM exam_records",
)
q(
    "warning_records（风险预警表）",
    "SELECT id, exam_record_id, warning_type, risk_score, risk_level, is_mock, reviewed FROM warning_records",
)
q(
    "security_events（安全事件表）",
    "SELECT id, event_type, username, ip, created_at FROM security_events ORDER BY id DESC LIMIT 5",
)

html = [f"""<!doctype html><html><head><meta charset="utf-8"><style>
body {{ font-family: -apple-system, 'PingFang SC', sans-serif; background:#1e1e2e; color:#e2e8f0; padding: 26px 34px; }}
h1 {{ font-size: 19px; }} .sub {{ color:#94a3b8; font-size:13px; margin-bottom:18px; }}
h2 {{ font-size:15px; color:#7dd3fc; margin: 20px 0 8px; }}
table {{ border-collapse: collapse; font-size: 12.5px; }}
th, td {{ border: 1px solid #475569; padding: 5px 10px; text-align: left; }}
th {{ background: #334155; }}
.prompt {{ color:#a5d6a7; font-size:12.5px; margin-bottom:4px; }}
</style></head><body>
<h1>MySQL 数据库 · exam_warning</h1>
<div class="sub">Server version: {ver} &nbsp;|&nbsp; Database: {db} &nbsp;|&nbsp; 真实查询结果</div>"""]

for title, cols, rows in sections:
    sqlish = title if not title.startswith("SHOW") else "SHOW TABLES"
    html.append(f'<div class="prompt">mysql&gt; {sqlish};</div><h2>{title}</h2>')
    html.append("<table><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>")
    for r in rows:
        html.append("<tr>" + "".join(f"<td>{'' if v is None else v}</td>" for v in r) + "</tr>")
    html.append("</table>")

html.append("</body></html>")

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/db_tables.html"
with open(out, "w") as f:
    f.write("\n".join(html))
print("written:", out)
