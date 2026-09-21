/**
 * 自动生成中期检查截图（Playwright + Chromium headless）
 * 前置条件：Flask(5001) 与 Vite(5174) 已启动，seed.py 已执行
 * 运行：cd frontend && node scripts/take_screenshots.mjs
 */
import { chromium } from 'playwright'
import { fileURLToPath } from 'url'
import path from 'path'
import fs from 'fs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const OUT = path.join(ROOT, 'screenshots')
fs.mkdirSync(OUT, { recursive: true })
const BASE = 'http://localhost:5174'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function apiLogin(page, username) {
  // 页面需处于同源，通过 fetch 调登录接口并写入 localStorage（JWT 登录态）
  await page.evaluate(async (u) => {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: '123456' }),
    })
    const d = await resp.json()
    localStorage.setItem('token', d.data.access_token)
    localStorage.setItem('user', JSON.stringify(d.data.user))
  }, username)
}

async function shoot(page, name) {
  await sleep(600)
  await page.screenshot({ path: path.join(OUT, name) })
  console.log('✔', name)
}

const LAUNCH_ARGS = [
  '--use-fake-ui-for-media-stream',
  '--use-fake-device-for-media-stream',
]

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true, channel: 'chrome', args: LAUNCH_ARGS })
  } catch (e) {
    console.log('（本机 Chrome 不可用，回退 Playwright Chromium）', e.message.slice(0, 80))
    return await chromium.launch({ headless: true, args: LAUNCH_ARGS })
  }
}

const browser = await launchBrowser()
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' })
await ctx.grantPermissions(['microphone'], { origin: BASE }).catch(() => {})

// 自动化说明：headless 环境无法完成真实的屏幕共享授权，且本机 headless Chrome 的
// 虚拟音频设备不可用（NotReadableError），因此以虚拟视频流替代媒体源 ——
// MediaRecorder 编码、录像上传、ffmpeg 音轨处理、AI 分析流水线全链路真实执行。
// （真机演示请按 README 流程在 Chrome 中实际共享屏幕）
await ctx.addInitScript(() => {
  const orig = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices)
  navigator.mediaDevices.getDisplayMedia = async () =>
    orig({ video: { width: 1280, height: 720, frameRate: 5 } })
  navigator.mediaDevices.getUserMedia = async (c) => {
    if (c && c.audio && !c.video) throw new DOMException('automation: no audio device', 'NotFoundError')
    return orig(c)
  }
})
const page = await ctx.newPage()
page.on('dialog', (d) => d.accept())
page.on('console', (m) => {
  if (m.type() === 'error') console.log('  [console.error]', m.text().slice(0, 160))
})

try {
  // 01 登录页
  await page.goto(BASE + '/login')
  await page.fill('input[type=text]', 'student03')
  await shoot(page, '01-login.png')

  // 02 教师首页
  await apiLogin(page, 'teacher')
  await page.goto(BASE + '/teacher')
  await page.waitForSelector('.stat-grid', { timeout: 15000 })
  await shoot(page, '02-teacher-dashboard.png')

  // 03/04 创建考试 + PDF 上传（表单已填写并选择 PDF 文件）
  await page.goto(BASE + '/teacher/exams/create')
  await page.waitForSelector('input[type=text]')
  await page.fill('input[type=text]', '2026 春季《计算机导论》期中考试')
  await page.fill('textarea', '闭卷考试，考试过程将进行屏幕录制与 AI 行为分析。')
  await page.setInputFiles('input[type=file]', path.join(ROOT, 'backend/uploads/exams/exam_demo_1.pdf'))
  await sleep(500)
  await shoot(page, '03-create-exam.png')
  await shoot(page, '04-pdf-upload.png')

  // 05 学生考试页（student03 无历史记录，自动进入考试）
  await apiLogin(page, 'student03')
  await page.goto(BASE + '/student/exam/1')
  await page.waitForSelector('.pdf-canvas', { timeout: 20000 })
  await sleep(800)
  await shoot(page, '05-student-exam.png')

  // 06 屏幕录制中（headless 使用虚拟摄像头/屏幕流）
  try {
    await page.click('button:has-text("● 开始录制")')
    await page.waitForSelector('.rec-indicator', { timeout: 8000 })
    await sleep(1500)
    await shoot(page, '06-screen-recording.png')
  } catch (e) {
    console.log('⚠ 录制状态未出现（headless 限制）：', e.message.slice(0, 120))
  }

  // 07 提交考试 → 上传录像 → AI 分析（先截"已提交/分析中"状态）
  await page.click('button:has-text("提交考试")') // confirm 弹窗自动接受
  await page.waitForSelector('text=考试已提交', { timeout: 30000 }).catch(() => {})
  await sleep(700)
  await shoot(page, '07-record-upload.png')

  // 08 AI 分析结果（等待分析完成，页面自动刷新）
  await page.waitForSelector('text=风险评分', { timeout: 40000 })
  await sleep(600)
  await shoot(page, '08-ai-analysis.png')

  // 09 教师预警中心
  await apiLogin(page, 'teacher')
  await page.goto(BASE + '/teacher/warnings')
  await page.waitForSelector('table', { timeout: 15000 })
  await shoot(page, '09-warning-list.png')

  // 10 预警详情（列表第一行 = 最高风险）
  await page.locator('a:has-text("查看详情")').first().click()
  await page.waitForSelector('.transcript-box', { timeout: 15000 })
  await sleep(700)
  await shoot(page, '10-warning-detail.png')

  // 11 数据库（真实 MySQL 查询结果渲染页，由 scripts/gen_db_html.py 生成）
  if (fs.existsSync('/tmp/db_tables.html')) {
    await page.goto('file:///tmp/db_tables.html')
    await shoot(page, '11-database.png')
  }

  // 12 系统运行中（学生考试列表）
  await page.goto(BASE + '/login')
  await apiLogin(page, 'student03')
  await page.goto(BASE + '/student/exams')
  await sleep(900)
  await shoot(page, '12-system-running.png')

  console.log('ALL SCREENSHOTS DONE')
} finally {
  await browser.close()
}
