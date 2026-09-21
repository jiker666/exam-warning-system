import { useEffect, useState } from 'react'
import { request } from '../../api/client.js'
import { AnalysisBadge } from '../../components/Badges.jsx'

export default function ScoreManagement() {
  const [records, setRecords] = useState(null)
  const [drafts, setDrafts] = useState({})
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  const load = () =>
    request({ url: '/records' }).then((r) => {
      setRecords(r.filter((x) => x.status === 'submitted'))
      const init = {}
      r.forEach((x) => (init[x.id] = x.score ?? ''))
      setDrafts(init)
    }).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [])

  const save = async (id) => {
    const value = drafts[id]
    if (value === '' || isNaN(Number(value))) return setError('成绩必须为 0 - 100 的数字')
    try {
      await request({ method: 'post', url: `/records/${id}/score`, data: { score: Number(value) } })
      setError('')
      setSaved(`记录 #${id} 成绩已保存：${value}`)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <h1 className="page-title">成绩管理</h1>
      <p className="page-sub">教师手工录入 / 修改学生考试成绩（暂不做自动阅卷）</p>

      {error && <div className="alert error">{error}</div>}
      {saved && <div className="alert ok">{saved}</div>}

      <div className="card">
        {!records ? (
          <div className="muted">加载中…</div>
        ) : records.length === 0 ? (
          <div className="muted center" style={{ padding: 30 }}>暂无已提交的考试记录</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>记录ID</th>
                  <th>学生</th>
                  <th>考试</th>
                  <th>提交时间</th>
                  <th>AI 分析</th>
                  <th>当前成绩</th>
                  <th>录入 / 修改</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>#{r.id}</td>
                    <td>{r.student_username}</td>
                    <td className="wrap">{r.exam_title}</td>
                    <td className="muted">{r.submit_time}</td>
                    <td><AnalysisBadge status={r.analysis_status} isMock={r.is_mock_analysis} /></td>
                    <td><b>{r.score ?? '—'}</b></td>
                    <td>
                      <span className="score-input">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="0.5"
                          value={drafts[r.id] ?? ''}
                          onChange={(e) => setDrafts({ ...drafts, [r.id]: e.target.value })}
                        />
                        <button className="btn sm" onClick={() => save(r.id)}>保存</button>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
