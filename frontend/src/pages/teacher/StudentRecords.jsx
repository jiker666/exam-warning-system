import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { request } from '../../api/client.js'
import { AnalysisBadge, RiskBadge, StatusBadge } from '../../components/Badges.jsx'
import { fmtScore } from '../../utils/format.js'

export default function StudentRecords() {
  const [params] = useSearchParams()
  const [records, setRecords] = useState(null)
  const [exams, setExams] = useState([])
  const [filterExam, setFilterExam] = useState(params.get('exam_id') || '')
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: '/exams' }).then(setExams).catch(() => {})
  }, [])

  const load = () => {
    const url = filterExam ? `/records?exam_id=${filterExam}` : '/records'
    request({ url }).then(setRecords).catch((e) => setError(e.message))
  }
  useEffect(() => {
    load()
  }, [filterExam])

  return (
    <div>
      <h1 className="page-title">学生考试记录</h1>
      <p className="page-sub">学生参加考试与 AI 分析情况总览（成绩录入请前往「成绩管理」）</p>

      <div className="filter-bar">
        <select value={filterExam} onChange={(e) => setFilterExam(e.target.value)}>
          <option value="">全部考试</option>
          {exams.map((e) => (
            <option key={e.id} value={e.id}>{e.title}</option>
          ))}
        </select>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="card">
        {!records ? (
          <div className="muted">加载中…</div>
        ) : records.length === 0 ? (
          <div className="muted center" style={{ padding: 30 }}>暂无学生考试记录</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>记录ID</th>
                  <th>学生</th>
                  <th>考试</th>
                  <th>开始时间</th>
                  <th>提交时间</th>
                  <th>状态</th>
                  <th>AI 分析</th>
                  <th>风险</th>
                  <th>成绩</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>#{r.id}</td>
                    <td>{r.student_username}</td>
                    <td className="wrap">{r.exam_title}</td>
                    <td className="muted">{r.start_time || '—'}</td>
                    <td className="muted">{r.submit_time || '—'}</td>
                    <td><StatusBadge status={r.status} /></td>
                    <td><AnalysisBadge status={r.analysis_status} isMock={r.is_mock_analysis} /></td>
                    <td>
                      <b>{r.risk_score}</b> <RiskBadge level={r.risk_level} />
                    </td>
                    <td>{fmtScore(r.score)}</td>
                    <td>
                      {r.warning_id ? (
                        <Link className="btn ghost light sm" to={`/teacher/warnings/${r.warning_id}`}>查看详情</Link>
                      ) : (
                        <span className="muted">—</span>
                      )}
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
