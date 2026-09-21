import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../../api/client.js'
import { examWindowText } from '../../utils/format.js'

export default function StudentHome() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: '/dashboard/student' }).then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="alert error">{error}</div>
  if (!data) return <div className="muted">加载中…</div>

  return (
    <div>
      <h1 className="page-title">学生首页</h1>
      <p className="page-sub">查看可参加的考试与自己的考试情况</p>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">可参加的考试</div>
          <div className="stat-value c-blue">{data.available_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">未完成的考试</div>
          <div className="stat-value c-orange">{data.not_submitted_count}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">已提交考试</div>
          <div className="stat-value c-green">{data.submitted_count}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title" style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ flex: 1 }}>可参加的考试</span>
          <Link to="/student/exams" className="btn ghost light sm">查看全部 →</Link>
        </div>
        {data.available_exams.length === 0 ? (
          <div className="muted center" style={{ padding: 26 }}>暂无可参加的考试</div>
        ) : (
          data.available_exams.map((e) => (
            <div key={e.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px dashed var(--border)' }}>
              <div style={{ flex: 1 }}>
                <b>{e.title}</b>
                <div className="muted">{examWindowText(e)}</div>
              </div>
              <Link className="btn sm" to={`/student/exam/${e.id}`}>进入考试</Link>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
