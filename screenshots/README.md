# 中期检查截图说明

截图由自动化脚本生成（真实页面 + 真实后端数据）：

```bash
# 前置：Flask(5001)、Vite(5174) 已启动，seed.py 已执行
cd backend && .venv/bin/python ../scripts/gen_db_html.py /tmp/db_tables.html   # 生成数据库展示页
cd frontend && node scripts/take_screenshots.mjs                               # 自动生成全部截图
```

## 截图清单

| 文件 | 内容 | 截取位置 / 状态 |
| ---- | ---- | ---- |
| `01-login.png` | 登录页 | `/login`，已填入演示账号，展示系统入口与演示账号说明 |
| `02-teacher-dashboard.png` | 教师首页 | `/teacher`，统计卡片（考试数/考试次数/待分析/预警数）+ 最新预警 + 安全事件 |
| `03-create-exam.png` | 创建考试 | `/teacher/exams/create`，表单已填写标题/说明/时间 |
| `04-pdf-upload.png` | PDF 上传 | 创建考试页，已选择 PDF 文件（显示文件名与大小），提交后自动逐页解析 |
| `05-student-exam.png` | 学生考试页 | `/student/exam/1`（student03），左侧试卷 PNG 分页查看 + 右侧录制/说明面板 |
| `06-screen-recording.png` | 屏幕录制中 | 考试页点击"● 开始录制"后，顶部 **● 正在录制 mm:ss** 红色呼吸指示 |
| `07-record-upload.png` | 录像上传/分析中 | 点击"提交考试"后，"AI 分析中"状态页 |
| `08-ai-analysis.png` | AI 分析结果 | 学生端"考试已提交"页：风险评分、等级、分析来源（Mock 有 ⚠ 徽标） |
| `09-warning-list.png` | AI 风险预警中心 | `/teacher/warnings`：学生/考试/风险分/等级/命中关键词/是否 Demo/复核状态 |
| `10-warning-detail.png` | 预警详情 | 预警中心第一行"查看详情"：学生/考试信息、风险评分环、命中关键词、转录原文、录像、复核表单 |
| `11-database.png` | 数据库 | 真实 MySQL 查询结果页（SHOW TABLES + 五张表数据，由 `scripts/gen_db_html.py` 生成） |
| `12-system-running.png` | 系统运行中 | 学生考试列表页（系统整体在用的状态） |

## 手动补拍建议（如需更真实的现场图）

- `06`：真机 Chrome 手动允许屏幕共享后截图（自动截图使用 Chromium 虚拟媒体流，UI 一致）
- `11`：也可用 Navicat/DataGrip/终端 `mysql -u root exam_warning` 连接后截图代替
