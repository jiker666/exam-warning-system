# AssemblyAI 真实 API 联调测试报告

> 本报告记录使用真实 AssemblyAI API 的转录测试，非 Mock 结果。测试脚本走项目自身的
> `backend/app/services/assemblyai_service.py`（`prepare_audio` + `transcribe`），
> 与业务链路完全一致，无任何绕过或伪装。出于安全考虑，本文不记录 API Key。

## 一、环境确认

| 配置项 | 值 | 说明 |
|---|---|---|
| `ASSEMBLYAI_API_KEY` | 已配置（32 位） | 存于 `.env`，不入库不入 git |
| `DEMO_MODE` | `false` | 未开启演示模式 |
| `TRANSCRIPT_LANGUAGE_CODE` | `zh` | 中文转录 |

- 测试时间：**2026-09-21 13:24:51 (CST)**
- 后端服务：Flask @ `localhost:5001`，`/api/health` 返回 `assemblyai_configured: true`

## 二、API Key 有效性验证

最小请求鉴权探测（GET `/v2/transcript/<不存在ID>`）：

| 请求 | HTTP 状态 | 结论 |
|---|---|---|
| 携带真实 Key | `400`（`transcript id not found`） | **鉴权通过**，仅 ID 不存在 |
| 不带 Key（对照组） | `401`（Unauthorized） | 鉴权层工作正常 |

**结论：Key 有效，`api.assemblyai.com` 可正常访问。**

## 三、真实语音转写测试

### 测试音频

- 来源：macOS TTS（婷婷 zh_CN）合成中文语音
- 长度：**16.0 秒**
- 格式：AIFF → ffmpeg 提取转换为 16kHz 单声道 MP3（与生产链路一致）
- 朗读内容（含指定测试语句）：

> 嗯，我看看这道题。**第二题答案是什么**？**这道题选什么**？是选A还是选C？喂，**告诉我答案**，快点告诉我答案。好，我自己再想想，这道题到底怎么做啊。

### 执行过程

1. `prepare_audio()`：ffmpeg 抽音轨 → 16kHz mono MP3 ✓
2. `POST /v2/upload`：音频上传成功，返回 `upload_url` ✓
3. `POST /v2/transcript`（`language_code=zh`）：任务创建成功，`id=297f2bd5-c5c6-4411-b34b-0e64efa0cfa0` ✓
4. 轮询 `GET /v2/transcript/{id}`：约 7.3 秒后 `status=completed` ✓

### 转录结果（真实 API 返回）

```
嗯，我看看这道题第二题答案是什么？这道题选什么？是选 A 还是选 C？ 喂，告诉我答案，快点告诉我答案。好，我自己再想想这道题到底怎么做啊？
```

- `source` = **`assemblyai`** ✓（非 `mock`）
- `is_mock` = **`false`** ✓
- 识别准确率：测试语句逐字命中，标点与数字格式略有差异（"选A"→"选 A"），属正常后处理

## 四、结论

| 检查项 | 结果 |
|---|---|
| 音频上传 | ✅ PASS |
| transcript task 创建 | ✅ PASS |
| 状态轮询 | ✅ PASS（7.3s completed） |
| 返回中文 transcript | ✅ PASS |
| `source == assemblyai` | ✅ PASS |
| `is_mock == false` | ✅ PASS |

**最终结果：PASS —— 真实 AssemblyAI API 联调成功。**

完整业务链路（WebM 上传→ffmpeg→转录→关键词→评分→落库→教师查看）的端到端验证见
`docs/test-report.md` 与 `screenshots/`。
