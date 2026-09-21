import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../../api/client.js'
import { RiskBadge } from '../../components/Badges.jsx'

const LEVELS = [
  { value: '', label: '全部等级' },
  { value: 'high', label: '高风险' },
  { value: 'medium', label: '中风险' },
  { value: 'low', label: '低风险' },
]

export default function WarningCenter() {
  const [warnings, setWarnings] = useState(null)
  const [stats, setStats] = useState(null)
  const [level, setLevel] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: '/warnings/stats' }).then(setStats).catch(() => {})
  }, [])

  useEffect(() => {
    const url = level ? `/warnings?risk_level=${level}` : '/warnings'
    request({ url }).then(setWarnings).catch((e) => setError(e.message))
  }, [level])

  return (
    <div>
      <h1 className="page-title">考试风险预警中心</h1>
      <p className="page-sub">
        基于 AssemblyAI 转录 + 关键词规则生成的考试行为预警，仅作为教师复核依据，不直接判定作弊
      </p>

      {stats && (
        <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-label">预警总数</div>
            <div className="stat-value">{stats.total}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">高风险</div>
            <div className="stat-value c-red">{stats.high}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">中风险</div>
            <div className="stat-value c-orange">{stats.medium}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">低风险</div>
            <div className="stat-value c-green">{stats.low}</div>
          </div>
        </div>
      )}

      <div className="filter-bar">
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          {LEVELS.map((l) => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </select>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="card">
        {!warnings ? (
          <div className="muted">加载中…</div>
        ) : warnings.length === 0 ? (
          <div className="muted center" style={{ padding: 30 }}>暂无预警记录</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>学生</th>
                  <th>考试</th>
                  <th>风险分</th>
                  <th>风险等级</th>
                  <th>命中关键词</th>
                  <th>状态</th>
                  <th>复核</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {warnings.map((w) => (
                  <tr key={w.id}>
                    <td>{w.student_username}</td>
                    <td className="wrap">{w.exam_title}</td>
                    <td><b>{w.risk_score}</b></td>
                    <td><RiskBadge level={w.risk_level} /></td>
                    <td className="wrap">
                      {w.hit_keywords.length === 0
                        ? <span className="muted">无命中</span>
                        : w.hit_keywords.slice(0, 3).map((h) => (
                            <span key={h.keyword} className="kw-chip">
                              {h.keyword} <b>×{h.count}</b>
                            </span>
                          ))}
                      {w.hit_keywords.length > 3 && (
                        <span className="muted"> 等 {w.hit_keywords.length} 项</span>
                      )}
                    </td>
                    <td>
                      {w.is_mock
                        ? <span className="badge mock">⚠ Demo 模拟</span>
                        : <span className="badge real">真实 AI</span>}
                    </td>
                    <td>{w.reviewed ? <span className="badge st-submitted">已复核</span> : <span className="muted">未复核</span>}</td>
                    <td>
                      <Link className="btn ghost light sm" to={`/teacher/warnings/${w.id}`}>查看详情</Link>
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
