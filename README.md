# 基于 AssemblyAI 的考试预警系统

大学生创新创业训练计划项目 · 在线考试过程录制与 AI 风险预警平台（中期检查版 MVP）

学生在浏览器参加考试并录制屏幕过程，提交后系统调用 **AssemblyAI** 完成语音转文字，基于可解释的关键词规则与风险评分生成"考试行为预警"，供教师复核。

> ⚠ AI 风险结果仅作为**考试行为预警 / 教师复核依据**，系统不直接判定学生作弊。

## 项目功能

- **教师端**：登录、Dashboard 统计、创建/编辑/发布考试、上传 PDF 试卷（自动逐页解析）、学生考试记录、AI 风险预警中心（风险分/等级/命中关键词/转录原文/录像回放/复核意见/重新分析）、成绩管理、安全事件（蜜罐）看板
- **学生端**：登录、考试列表、在线考试（试卷分页查看）、屏幕录制（`getDisplayMedia + MediaRecorder`，屏幕声音+麦克风混音）、提交考试并上传录像、查看 AI 分析状态
- **AI 分析**：录像 → ffmpeg 提取音轨 → AssemblyAI 转录 → 关键词检测 → 风险评分（0-100，低/中/高）→ 预警记录
- **Demo 模式**：未配置 API Key 或开启 `DEMO_MODE` 时自动使用预置模拟转录，界面/数据库/接口**三处明确标记 Mock**，不冒充真实结果

## 技术栈

| 端 | 技术 |
| ---- | ---- |
| 前端 | React 18、Vite、React Router、Axios、原生 CSS |
| 后端 | Python、Flask、Flask-SQLAlchemy、Flask-JWT-Extended、Flask-CORS |
| 数据库 | MySQL 8（SQLAlchemy ORM，可退回 SQLite） |
| 关键库 | PyMuPDF（PDF 渲染）、requests（AssemblyAI 纯 HTTP 集成）、ffmpeg（音轨提取，可选） |

## 系统架构

见 `docs/architecture.md`（含 Mermaid 系统架构图与 AI 分析流程图）。

## 项目目录

```text
assemblyAI/
├── backend/
│   ├── app/
│   │   ├── models/          # users / exams / exam_records / warning_records / security_events
│   │   ├── routes/          # auth / exams / records / warnings / dashboard / security
│   │   ├── services/        # pdf_service / assemblyai_service / risk_rules / analysis_service
│   │   ├── utils/           # 统一返回 / 角色守卫 / 文件安全 / IDOR 校验
│   │   └── __init__.py      # 应用工厂 / 统一异常处理
│   ├── uploads/             # exams(PDF) / exam_images(PNG) / recordings(WebM)
│   ├── tests/               # pytest（单元 + 全链路集成）
│   ├── config.py / run.py / seed.py / requirements.txt
├── frontend/
│   ├── src/api/             # Axios 客户端（JWT 自动附加 / 401 跳转）
│   ├── src/pages/           # teacher×7 / student×3 / login
│   ├── src/router/ src/components/ src/utils/
│   └── scripts/take_screenshots.mjs   # 自动截图脚本
├── docs/                    # architecture / database / api / test-report / midterm-material
├── scripts/                 # init_mysql.sql / gen_db_html.py
├── screenshots/             # 中期检查截图
├── .env.example
└── README.md
```

## 环境要求

- Python ≥ 3.10，Node.js ≥ 18，MySQL 8.x（或使用 SQLite 兜底）
- 演示屏幕录制需 Chrome/Edge（浏览器策略要求 `localhost` 或 HTTPS）
- 可选：ffmpeg（用于从录像提取音轨；未安装时直接上传原录像，AssemblyAI 亦支持）

## MySQL 初始化

```bash
# 1. 建库（root 无密码的本地开发环境）
mysql -u root < scripts/init_mysql.sql
# 若 root 有密码，请修改 .env 中 DATABASE_URL 后再执行（含密码）

# 2. 建表在应用启动时自动完成（db.create_all）
# 3. 写入演示数据（可重复执行，幂等）
cd backend && python seed.py
```

> 无 MySQL 时：`.env` 里设 `DATABASE_URL=sqlite:///backend/app.db`，其余步骤不变。

## 后端启动

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp ../.env.example ../.env      # 首次：按需修改配置
.venv/bin/python run.py         # 默认 http://localhost:5001
```

## 前端启动

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5174 （/api 代理至 5001）
```

> 端口说明：macOS 5000 常被 AirPlay 占用故后端用 5001；本机 5173 被占用故前端用 5174（见 `vite.config.js`）。

## AssemblyAI 配置

1. 在 https://www.assemblyai.com/ 注册并获取 API Key（有免费额度）
2. 编辑 `.env`：

```env
ASSEMBLYAI_API_KEY=你的Key
TRANSCRIPT_LANGUAGE_CODE=zh     # 异常关键词为中文
DEMO_MODE=false
```

3. 重启后端即可切换真实转录，**无需改代码**

| 场景 | 行为 |
| ---- | ---- |
| 配置了 Key 且未开 DEMO_MODE | 真实调用 AssemblyAI（上传音频→创建转录→轮询结果） |
| 未配置 Key | 自动 Mock 模式，分析结果三处标记 "Mock Result / ⚠ Demo 模拟分析" |
| Key 配置但调用失败 | 该记录 `analysis_status=failed` 并记录原因，教师可在预警详情页点"重新 AI 分析" |
| `DEMO_MODE=true` | 强制 Mock（现场演示兜底，即使配了 Key） |

## Demo 数据

`seed.py` 创建（密码均为 `123456`，仅本地演示用）：

| 账号 | 角色 | 预置数据 |
| ---- | ---- | ---- |
| `teacher` | 教师 | 创建了已发布的"Demo 在线考试"（自动生成 2 页试卷 PDF） |
| `student01` | 学生 | 一条已提交记录 + **Mock 高风险预警**（演示预警中心效果，明确标记） |
| `student02` | 学生 | 一条已提交记录，正常低风险，已录成绩 88 |
| `student03` | 学生 | **无记录**（用于现场演示完整流程：进入考试→录制→提交→AI 分析） |

## 默认测试账号

见上表。教师 `teacher/123456`，学生 `student01~03/123456`。

## 测试方式

```bash
# 后端自动化测试（10 项：单元 8 + 全链路集成 2）
cd backend && .venv/bin/python -m pytest tests/ -v

# 前端构建检查
cd frontend && npm run build

# 全链路 API 手工演练（可选，需先启动前后端）
# 按 docs/test-report.md 中的步骤，或参考 tests/test_api_flow.py
```

## 中期演示流程（现场 5 分钟版）

1. **启动**：MySQL 已运行 → `cd backend && .venv/bin/python run.py` → `cd frontend && npm run dev`
2. **教师登录**（teacher/123456）→ Dashboard 展示统计与安全事件
3. **创建考试**：填写标题 → 选择一个 PDF → 创建 → 发布（也可直接用预置 Demo 考试）
4. **学生登录**（student03/123456）→ 考试列表 → 进入考试
5. 点击 **● 开始录制** → 浏览器弹出屏幕共享 → 选择"整个屏幕"→ 允许（含麦克风）
6. 页面显示 **● 正在录制 00:xx**，翻页查看试卷作答
7. 点击 **提交考试** → 确认 → 录像自动上传 → 页面显示"AI 分析中"
8. 等待数秒，页面显示**风险评分与等级**（Mock 模式会显示 ⚠ Demo 模拟分析徽标）
9. 切回教师 → **AI 风险预警中心** → 看到新预警 → **查看详情**：转录原文、命中关键词、风险分、录像回放
10. 填写**复核意见**保存；（可选）演示成绩管理、蜜罐事件

> 若现场网络不稳，`.env` 中设 `DEMO_MODE=true` 重启后端，保证 Mock 分析确定性演示。

## 更多文档

- `docs/architecture.md` 系统架构 / `docs/database.md` 数据库设计 / `docs/api.md` API
- `docs/test-report.md` 测试报告 / `docs/midterm-material.md` 中期材料 / `FINAL_REPORT.md` 交付总结
- `screenshots/README.md` 截图说明（`frontend/scripts/take_screenshots.mjs` 可自动重新生成）
