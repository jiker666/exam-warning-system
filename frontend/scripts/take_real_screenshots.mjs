// 真实 AssemblyAI 联调截图：基于 record#12（真实转录，is_mock=false）
import { chromium } from 'playwright'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT = path.resolve(__dirname, '../../screenshots')
const BASE = 'http://localhost:5174'

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN' })
const page = await ctx.newPage()
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function apiLogin(p, username) {
  await p.evaluate(async (u) => {
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
const shoot = (name) => page.screenshot({ path: `${OUT}/${name}`, fullPage: true })

// 1. 学生已提交视图：真实 AI 分析结果（无 Mock 徽标）
await page.goto(BASE + '/login')
await apiLogin(page, 'student03')
await page.goto(BASE + '/student/exam/3')
await page.waitForSelector('text=风险评分', { timeout: 40000 })
await sleep(900)
await shoot('08-ai-analysis.png')
console.log('✔ 08-ai-analysis.png')

// 2. 学生考试记录（我的记录，真实完成）
await page.goto(BASE + '/student')
await page.waitForLoadState('networkidle')
await sleep(1200)
await shoot('12-system-running.png')
console.log('✔ 12-system-running.png')

// 3. 教师 AI 风险预警中心（仅真实预警行）
await page.goto(BASE + '/login')
await apiLogin(page, 'teacher')
await page.goto(BASE + '/teacher/warnings')
await page.waitForSelector('table', { timeout: 15000 })
await sleep(700)
await shoot('09-warning-list.png')
console.log('✔ 09-warning-list.png')

// 4. 预警详情：真实 Transcript + 风险评分 + 命中关键词
await page.locator('a:has-text("查看详情")').first().click()
await page.waitForSelector('.transcript-box', { timeout: 15000 })
await sleep(800)
await shoot('10-warning-detail.png')
console.log('✔ 10-warning-detail.png')

// 5. 真实 Transcript 特写（完整文本）
await page.locator('.transcript-box').screenshot({ path: `${OUT}/13-real-transcript.png` })
console.log('✔ 13-real-transcript.png')

// 6. 教师端学生考试记录
await page.goto(BASE + '/teacher/records')
await page.waitForSelector('table', { timeout: 15000 })
await sleep(700)
await shoot('14-teacher-records.png')
console.log('✔ 14-teacher-records.png')

await browser.close()
console.log('REAL SCREENSHOTS DONE')
