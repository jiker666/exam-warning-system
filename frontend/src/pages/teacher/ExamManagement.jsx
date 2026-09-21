import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../../api/client.js'
import { StatusBadge } from '../../components/Badges.jsx'
import { examWindowText } from '../../utils/format.js'

export default function ExamManagement() {
  const [exams, setExams] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const load = () => request({ url: '/exams' }).then(setExams).catch((e) => setError(e.message))
  useEffect(() => {
    load()
  }, [])

  const publish = async (id) => {
    try {
      await request({ method: 'post', url: `/exams/${id}/publish` })
      setMsg('考试已发布，学生端可见')
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 className="page-title" style={{ flex: 1 }}>考试管理</h1>
        <Link to="/teacher/exams/create" className="btn">+ 创建考试</Link>
      </div>
      <p className="page-sub">管理已创建的考试，上传试卷并发布给学生</p>

      {msg && <div className="alert ok">{msg}</div>}
      {error && <div className="alert error">{error}</div>}

      <div className="card">
        {!exams ? (
          <div className="muted">加载中…</div>
        ) : exams.length === 0 ? (
          <div className="muted center" style={{ padding: 30 }}>
            还没有创建考试，点击右上角「创建考试」开始
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>考试标题</th>
                  <th>考试时间</th>
                  <th>试卷页数</th>
                  <th>状态</th>
                  <th>提交情况</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {exams.map((e) => (
                  <tr key={e.id}>
                    <td>{e.id}</td>
                    <td className="wrap">{e.title}</td>
                    <td className="muted">{examWindowText(e)}</td>
                    <td>{e.page_count} 页</td>
                    <td><StatusBadge status={e.status} /></td>
                    <td>
                      {e.submitted_count ?? 0} / {e.record_count ?? 0} 已提交
                    </td>
                    <td>
                      <span style={{ display: 'inline-flex', gap: 6, flexWrap: 'wrap' }}>
                        {e.status === 'draft' && (
                          <button className="btn sm success" onClick={() => publish(e.id)}>发布</button>
                        )}
                        <Link className="btn ghost light sm" to={`/teacher/records?exam_id=${e.id}`}>考试记录</Link>
                        <Link className="btn ghost light sm" to={`/teacher/exams/${e.id}/edit`}>编辑</Link>
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
