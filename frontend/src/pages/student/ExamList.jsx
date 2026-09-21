import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../../api/client.js'
import { StatusBadge } from '../../components/Badges.jsx'
import { examOpenState, examWindowText } from '../../utils/format.js'

export default function ExamList() {
  const [exams, setExams] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: '/exams' }).then(setExams).catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <h1 className="page-title">考试列表</h1>
      <p className="page-sub">已发布的在线考试；进入考试后请允许屏幕共享以开始过程录制</p>
      {error && <div className="alert error">{error}</div>}

      {!exams ? (
        <div className="muted">加载中…</div>
      ) : exams.length === 0 ? (
        <div className="card muted center" style={{ padding: 40 }}>暂无可参加的考试</div>
      ) : (
        <div className="exam-grid">
          {exams.map((e) => {
            const state = examOpenState(e)
            const submitted = e.my_record?.status === 'submitted'
            return (
              <div className="exam-card" key={e.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ flex: 1 }}>{e.title}</h3>
                  {submitted && <StatusBadge status="submitted" />}
                </div>
                <div className="desc">{e.description || '（无考试说明）'}</div>
                <div className="meta">考试时间：{examWindowText(e)}</div>
                <div className="meta">试卷：{e.page_count} 页 · 当前状态：<b style={state.open ? { color: 'var(--success)' } : { color: 'var(--text-2)' }}>{state.label}</b></div>
                <div style={{ marginTop: 6 }}>
                  {submitted ? (
                    <Link className="btn ghost light sm" to={`/student/exam/${e.id}`}>查看考试结果</Link>
                  ) : state.open ? (
                    <Link className="btn sm" to={`/student/exam/${e.id}`}>进入考试 →</Link>
                  ) : (
                    <button className="btn ghost light sm" disabled>{state.label}</button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
