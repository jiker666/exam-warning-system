# FINAL_REPORT — 基于 AssemblyAI 的考试预警系统（中期 MVP）

> 生成：2026-09-21 · 本报告严格描述当前真实完成情况

## 1. 项目是否可以运行

**可以。** 当前机器已完成完整验证：

- 后端 pytest **10/10 通过**（单元 + 全链路集成）
- 真实 MySQL 8.4 落库，seed 数据就绪
- 前端 `npm run build` 通过
- Playwright + Chrome 自动化完成**浏览器端全流程**（登录→建考→发布→学生录制→提交上传→AI 分析→预警查看），12 张截图存于 `screenshots/`

## 2. 前后端地址

| 服务 | 地址 | 说明 |
| ---- | ---- | ---- |
| 前端 | http://localhost:5174 | Vite 开发服务器（5173 被本机其他进程占用）；`/api` 自动代理到后端 |
| 后端 | http://localhost:5001 | Flask（macOS 5000 被 AirPlay 占用）；健康检查 `/api/health` |

## 3. 测试账号（seed.py 创建，密码均 `123456`）

| 账号 | 角色 | 用途 |
| ---- | ---- | ---- |
| teacher | 教师 | 演示教师端全部功能（已预置 1 场已发布 Demo 考试） |
| student01 | 学生 | 预置一条 **Mock 高风险预警** 记录（预警中心演示） |
| student02 | 学生 | 预置一条正常记录，已录成绩 88 |
| student03 | 学生 | **无记录**，现场演示完整流程专用 |

## 4. MySQL 初始化方法

```bash
mysql -u root < scripts/init_mysql.sql   # 建库 exam_warning
cd backend && .venv/bin/python seed.py   # 建表(自动) + 演示数据(幂等)
```

（本机 MySQL 8.4 root 免密；有密码时改 `.env` 的 `DATABASE_URL`。）

## 5. AssemblyAI 配置方法

`.env` 中设置 `ASSEMBLYAI_API_KEY=<你的Key>`（https://www.assemblyai.com/ 免费额度），`DEMO_MODE=false`，重启后端即切换真实转录，无需改代码。

> **✅ 真实 API 已验证（2026-09-21）**：16 秒中文语音 7.3 秒完成真实转录（识别准确）；完整业务链路（学生提交含真实语音的 WebM → ffmpeg 提音轨 → 真实转录 → 命中"答案是什么/告诉我答案/选什么"等关键词 → 风险分 80/高风险 → 预警落库 `is_mock=0`）端到端验证通过。证据：`docs/assemblyai-real-test.md`、`docs/test-report.md` 第 7 节、真实截图 `08/09/10/12/13/14`。

## 6. 已实现功能（全部运行验证）

- JWT 登录认证、教师/学生角色守卫、登录失效自动跳转
- 教师端：Dashboard 统计、创建/编辑/发布考试、PDF 上传与逐页解析、学生考试记录、AI 风险预警中心（列表/详情/转录/命中关键词/录像回放/复核意见/重新分析）、成绩管理、安全事件看板
- 学生端：考试列表、在线考试（试卷分页）、屏幕录制（getDisplayMedia+MediaRecorder、屏幕音+麦克风混音）、提交与录像上传（进度显示）、分析状态轮询与结果展示
- AI 分析流水线：录像→ffmpeg 提取音轨→AssemblyAI（纯 HTTP）→关键词检测（risk_rules.py 统一维护）→风险评分（可解释规则）→预警落库；分析状态机 pending/processing/completed/failed
- 安全：密码哈希、ORM、上传白名单/大小/随机名、IDOR 防护（记录/录像/预警）、Honeypot 蜜罐（隐藏字段+诱捕接口）+ 安全事件记录
- Demo/Mock 模式：无 Key 或 DEMO_MODE=true 时使用预置模拟转录，数据库/接口/界面三处标记 "Mock Result / ⚠ Demo 模拟分析"，绝不冒充真实结果

## 7. 未实现功能（如实）

- 真实 AssemblyAI 接口**调用代码已实现但未用真实 Key 实测**（无 Key；配置后即用）
- 学生注册/找回密码/验证码/OAuth/复杂 RBAC（按需求明确排除）
- 自动阅卷、人脸/眼球/姿态识别（按需求明确排除）
- 生产化部署（Nginx/gunicorn/Docker）、任务队列、并发压测
- 统计图表、视频画面级行为分析（P2，未开始）

## 8. 已知问题

1. 外部 AI API 依赖网络与 Key；失败时记录标记 failed，可在预警详情页重新分析
2. 屏幕录制依赖 Chrome/Edge + localhost/HTTPS；iOS Safari 不支持 getDisplayMedia
3. 关键词规则存在误报/漏报（如"查一下"命中正常自语）；仅作复核依据
4. 重新开始录制会覆盖之前片段（UI 已提示）
5. 分析为进程内后台线程，服务器重启会中断进行中的分析（可重新触发）
6. 自动化截图使用虚拟视频流替代真实屏幕共享（受 headless 环境限制，已在 screenshots/README.md 说明；真机演示不受影响）

## 9. 中期演示步骤

见 `README.md`「中期演示流程」（5 分钟版，从启动到教师查看预警详情）。

## 10. 中期截图页面

12 张已生成于 `screenshots/`（清单见 `screenshots/README.md`），覆盖登录、教师 Dashboard、创建考试、PDF 上传、学生考试、录制中、上传/分析、AI 结果、预警中心、预警详情、数据库、系统运行。

## 11. 中期检查表可填写的阶段性成果

见 `docs/midterm-material.md` 第三节（7 条，可直接复制）：完整技术链路 MVP、浏览器录制方案、AssemblyAI 服务集成、可解释风险评分模型、预警复核闭环、安全设计、自动化测试与文档体系。

## 12. 代码统计

- 后端：Python ~1500 行（25 个 API，4 个服务模块，5 张表）
- 前端：React ~2200 行（12 个页面）
- 测试：pytest 10 项全过；Playwright 自动化截图脚本
- Git：4 个里程碑提交（backend MVP / frontend / docs+screenshots / final）
