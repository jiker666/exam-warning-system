/** 通用小工具：风险等级文案、考试时间窗口文案等 */

export function riskText(level) {
  return { high: '高风险', medium: '中风险', low: '低风险' }[level] || level
}

export function examWindowText(exam) {
  const start = exam?.start_time
  const end = exam?.end_time
  if (!start && !end) return '不限时间（随时可参加）'
  if (start && end) return `${start} ~ ${end}`
  if (start) return `${start} 开始`
  return `${end} 截止`
}

export function examOpenState(exam) {
  if (exam.status !== 'published') return { label: '未发布', open: false }
  if (exam.is_open) return { label: '进行中 · 可进入', open: true }
  const now = new Date()
  if (exam.start_time && new Date(exam.start_time.replace(' ', 'T')) > now)
    return { label: '未开始', open: false }
  return { label: '已结束', open: false }
}

export function fmtScore(score) {
  return score === null || score === undefined ? '—' : score
}
