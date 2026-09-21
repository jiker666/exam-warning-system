# 测试报告

> 记录时间：2026-09-21。所有 PASS 项均有真实运行证据（pytest 输出 / curl 实际返回），
> 禁止虚构：尚未用真实 AssemblyAI Key 验证的项目明确标注为"未验证"。

## 0. 测试环境

- macOS (Darwin 23.6.0, Apple Silicon) / Python 3.13 / Node 22 / MySQL 8.4.9（Homebrew 服务）
- 后端测试命令：`cd backend && .venv/bin/python -m pytest tests/ -v`
- **自动化测试结果：10 passed（risk_rules 单元 8 项 + API 全链路集成 2 项）**

---

## 1. 登录测试

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 正确账号登录成功返回 JWT；错误密码被拒绝；未登录访问受保护接口返回 401 |
| 测试步骤 | ① POST `/api/auth/login` 正确密码 ② 错误密码 ③ 不带 token GET `/api/exams` |
| 预期结果 | ① code=0 且返回 access_token ② HTTP 401 ③ HTTP 401 |
| 实际结果 | ① token 正常获取（curl 与 pytest 均验证）② `用户名或密码错误` 401 ③ 401 `未登录或缺少访问令牌` |
| 是否通过 | **PASS**（pytest `test_full_pipeline` + curl 演练） |

## 2. 创建考试

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 教师创建考试（含 PDF）成功；学生创建考试被 403 拒绝 |
| 测试步骤 | ① 教师 token POST `/api/exams`（multipart 带 PDF）② 学生 token 同样请求 |
| 预期结果 | ① 创建成功返回考试对象（page_count=2）② 403 |
| 实际结果 | ① `exam id=2 pages=2`（curl 演练输出）② pytest 断言 403 通过 |
| 是否通过 | **PASS** |

## 3. PDF 上传与解析

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | PDF 保存成功并被 PyMuPDF 逐页渲染为 PNG |
| 测试步骤 | 创建考试时上传 2 页 PDF → 检查 `page_count` 与 `uploads/exam_images/<id>/` |
| 预期结果 | page_count=2，生成 page_1.png / page_2.png |
| 实际结果 | pytest 断言 page_count==2；curl 演练 `page1 http: 200 type: image/png size: 56969` |
| 是否通过 | **PASS** |

## 4. PDF 展示（学生端）

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 学生端考试页分页展示试卷图片（上一页/下一页/页码） |
| 测试步骤 | ① 学生 token 经前端代理 GET `/api/exams/1/pages/1` ② 浏览器打开考试页（Playwright 自动化） |
| 预期结果 | ① 200 image/png ② 页面渲染 `.pdf-canvas` 且可翻页 |
| 实际结果 | ① 通过（Vite 5174 代理，带 JWT）② Playwright `waitForSelector('.pdf-canvas')` 通过并截图 `05-student-exam.png` |
| 是否通过 | **PASS** |

## 5. 屏幕录制

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 浏览器 `getDisplayMedia + MediaRecorder` 录制，界面显示"● 正在录制" |
| 测试步骤 | 考试页点击"● 开始录制" → 授权屏幕共享 |
| 预期结果 | 出现录制指示器与计时 |
| 实际结果 | Playwright（Chromium 虚拟媒体流）`waitForSelector('.rec-indicator')` 通过，截图 `06-screen-recording.png`。真机手动验证建议在演示前用 Chrome 实际走一遍（见 README 演示流程） |
| 是否通过 | **PASS**（自动化虚拟流；真机演示步骤见 README） |

## 6. 文件上传（考试录像）

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 提交考试时上传 WebM 录像至服务器 |
| 测试步骤 | ① ffmpeg 生成真实 webm（含音轨）→ curl 提交 ② Playwright 浏览器内录制后提交 |
| 预期结果 | 上传成功，返回 `analysis_triggered: true` |
| 实际结果 | ① `考试提交成功` + 分析完成 ② 浏览器内录制 Blob 上传成功并进入分析流程 |
| 是否通过 | **PASS** |

## 7. AssemblyAI 转录

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 转录服务独立于业务；无 Key 时进入 Mock 且**明确标记** |
| 测试步骤 | ① 无 Key 环境提交录像 → 轮询 analysis_status ② 检查 warning.is_mock 与 analysis_note |
| 预期结果 | ① pending → processing → completed ② is_mock=True，note 含 "Mock Result" 字样 |
| 实际结果 | ① `[1] processing → [2] completed`（curl 演练）② pytest 断言 is_mock_analysis 为 True 通过 |
| 是否通过 | **PASS（Mock 模式）**。⚠ 未验证项：**真实 AssemblyAI API 调用**（需配置 API Key 后验证，代码路径已实现，配置方法见 README「AssemblyAI 配置」） |

## 8. 风险评分

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 关键词计分、封顶、等级划分正确 |
| 测试步骤 | risk_rules 单元测试 8 项（含大小写、单词封顶 3 次、总分封顶 100、长词优先防重复计分、阈值 30/60） |
| 预期结果 | 全部断言通过 |
| 实际结果 | **8 项全部 PASS**；E2E 中演示数据评分与规则一致（如种子高风险样例 100 分） |
| 是否通过 | **PASS** |

## 9. 预警生成与教师查看

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 分析完成后生成 warning_records；教师预警中心可查询 |
| 测试步骤 | ① 学生提交 → 教师 GET `/api/warnings` ② GET `/api/warnings/{id}` 详情 |
| 预期结果 | 列表含学生/考试/风险分/命中关键词/是否 Mock；详情含 transcript |
| 实际结果 | curl 演练输出 warning 记录完整；pytest 断言列表与详情字段通过 |
| 是否通过 | **PASS** |

## 10. 权限测试（角色隔离）

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 学生不能访问教师接口，教师接口有角色守卫 |
| 测试步骤 | ① 学生 POST `/api/exams` ② 学生 GET `/api/warnings` ③ 学生 GET `/api/dashboard/teacher` |
| 预期结果 | 均 403 |
| 实际结果 | pytest 断言全部 403 通过 |
| 是否通过 | **PASS** |

## 11. IDOR 测试

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 学生 B 不能访问学生 A 的考试记录/录像（遍历 record_id 无效） |
| 测试步骤 | s2 token 访问 s1 的 `GET /api/records/{id}` 与 `/recording` |
| 预期结果 | 均 403 |
| 实际结果 | pytest 断言 403 通过 |
| 是否通过 | **PASS** |

## 12. Honeypot 蜜罐测试

| 项 | 内容 |
| ---- | ---- |
| 测试目标 | 提交蜜罐字段 / 访问诱捕接口被记录为安全事件 |
| 测试步骤 | ① submit 携带 `contact_email_backup=bot@example.com` ② GET `/api/admin/backup-keys` ③ 教师 GET `/api/security/events` |
| 预期结果 | ① 403 ② ③ 事件列表包含两类事件 |
| 实际结果 | pytest `test_honeypot_field_logged_on_submit` 通过；curl 触发后教师 Dashboard「安全事件」卡片可见 |
| 是否通过 | **PASS** |

## 13. 未验证 / 已知限制（如实说明）

1. **真实 AssemblyAI 转录未验证**：本机未配置 API Key。真实模式代码路径（上传音频 → 创建任务 → 轮询）已实现，配置 `.env` 中 `ASSEMBLYAI_API_KEY` 后即切换；若 Key 无效/网络失败，记录会标记 `failed` 并可在预警详情页重新触发分析。
2. 屏幕录制的真机表现依赖浏览器（Chrome/Edge 支持 getDisplayMedia；需 localhost 或 HTTPS 环境）。
3. 风险模型为关键词规则版（中期目标），误报/漏报存在，仅作复核参考。
