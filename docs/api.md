# API 文档

- Base URL：`http://localhost:5001/api`（前端通过 Vite 代理 `/api` 转发）
- 认证：除登录与蜜罐接口外，均需请求头 `Authorization: Bearer <access_token>`
- 统一返回格式：

```json
{ "code": 0, "message": "success", "data": { } }
```

失败时 `code` 非 0，HTTP 状态码同步（400 参数错误 / 401 未登录或密码错 / 403 无权限 / 404 不存在）。

## 1. 认证 auth

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| POST | `/auth/login` | 公开 | JSON: `username, password` | `access_token, user` | 登录 |
| GET | `/auth/me` | 已登录 | — | 用户信息 + token claims | 当前用户 |

## 2. 考试 exams

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| GET | `/exams` | 教师/学生 | — | 考试数组（教师=自己创建的全部；学生=已发布的，附 `my_record`） | 考试列表 |
| POST | `/exams` | 教师 | multipart: `title, description?, start_time?, end_time?, pdf`（≤20MB） | 考试对象（含 `page_count`） | 创建考试并解析 PDF |
| GET | `/exams/{id}` | 教师(本人)/学生(已发布) | — | 考试详情 | 考试详情 |
| PUT | `/exams/{id}` | 教师(本人) | 同 POST，pdf 可选（替换则重新渲染） | 考试对象 | 编辑考试 |
| POST | `/exams/{id}/publish` | 教师(本人) | — | 考试对象 | 发布考试 |
| GET | `/exams/{id}/pages` | 教师(本人)/学生(已发布) | — | `{page_count, pages:[{page,url}]}` | 试卷分页索引 |
| GET | `/exams/{id}/pages/{n}` | 同上 | — | PNG 图片 | 试卷第 n 页图片 |
| GET | `/exams/{id}/pdf` | 同上 | — | PDF 文件 | 下载原 PDF |
| GET | `/exams/{id}/records` | 教师(本人) | — | 记录数组 | 该考试的学生记录 |

## 3. 考试记录 records

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| POST | `/records` | 学生 | JSON: `exam_id` | 记录对象 | 进入考试（创建/恢复进行中记录） |
| GET | `/records/mine` | 学生 | — | 记录数组 | 我的考试记录 |
| GET | `/records` | 教师 | query: `exam_id?` | 记录数组 | 教师查看全部学生记录 |
| GET | `/records/{id}` | 学生(本人)/教师(本场) | — | 记录 + warnings + exam | 记录详情（IDOR 校验） |
| POST | `/records/{id}/submit` | 学生(本人) | multipart: `recording`（webm 等，≤500MB）+ 蜜罐字段 `contact_email_backup` | 记录对象（`analysis_triggered`） | 提交考试并上传录像，触发 AI 分析 |
| POST | `/records/{id}/score` | 教师(本场) | JSON: `score`(0-100) | 记录对象 | 录入/修改成绩 |
| POST | `/records/{id}/analyze` | 教师(本场) | — | 记录对象 | 重新触发 AI 分析 |
| GET | `/records/{id}/recording` | 学生(本人)/教师(本场) | — | WebM 视频 | 考试录像回放（IDOR 校验） |

## 4. 风险预警 warnings（均教师）

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| GET | `/warnings` | 教师(本人考试) | query: `risk_level?`, `exam_id?` | 预警摘要数组（含学生/考试/命中关键词/是否Mock） | 预警中心列表 |
| GET | `/warnings/stats` | 教师 | — | `{total, low, medium, high}` | 预警统计 |
| GET | `/warnings/{id}` | 教师(本人考试) | — | 预警详情 + record + exam + student | 预警详情 |
| POST | `/warnings/{id}/review` | 教师(本人考试) | JSON: `review_note` | 预警对象 | 保存教师复核意见 |

## 5. 仪表盘 dashboard

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| GET | `/dashboard/teacher` | 教师 | — | 考试数/提交数/待分析/预警数/最近预警/安全事件 | 教师 Dashboard |
| GET | `/dashboard/student` | 学生 | — | 可参加数/已完成数等 | 学生首页 |

## 6. 安全 security

| Method | URL | 权限 | 参数 | 返回 data | 功能 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| GET | `/admin/backup-keys` | 公开（蜜罐） | — | 403 | 诱捕接口：任何访问记录为安全事件 |
| GET | `/security/events` | 教师 | — | 事件数组 | 查看安全事件 |

> 蜜罐隐藏字段 `contact_email_backup` 随考试提交接口检测：非空即记录 `honeypot_field` 安全事件。

## 7. 其他

| Method | URL | 说明 |
| ---- | ---- | ---- |
| GET | `/health` | 健康检查（返回 demo_mode / 是否配置 AssemblyAI Key） |
