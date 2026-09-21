import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../../api/client.js'
import { RiskBadge } from '../../components/Badges.jsx'

export default function TeacherDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: '/dashboard/teacher' }).then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="alert error">{error}</div>
  if (!data) return <div className="muted">加载中…</div>

  return (
    <div>
      <h1 className="page-title">教师 Dashboard</h1>
      <p className="page-sub">考试数量、学生考试情况与 AI 风险预警总览</p>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">考试数量</div>
          <div className="stat-value c-blue">{data.exam_count}</div>
          <div className="stat-hint">已发布 {data.published_count} 场</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">学生考试次数</div>
          <div className="stat-value c-green">{data.record_count}</div>
          <div className="stat-hint">已提交的考试记录</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">待分析数量</div>
          <div className="stat-value c-orange">{data.pending_analysis}</div>
          <div className="stat-hint">pending / processing</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">风险预警数量</div>
          <div className="stat-value c-red">{data.warning_count}</div>
          <div className="stat-hint">其中高风险 {data.high_risk_count} 条</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">最新风险预警</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>学生</th>
                <th>考试</th>
                <th>风险分</th>
                <th>风险等级</th>
                <th>分析状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_warnings.length === 0 && (
                <tr>
                  <td colSpan="6" className="muted center">暂无预警记录</td>
                </tr>
              )}
              {data.recent_warnings.map((w) => (
                <tr key={w.id}>
                  <td>{w.student_username}</td>
                  <td className="wrap">{w.exam_title}</td>
                  <td>
                    <b>{w.risk_score}</b>
                  </td>
                  <td>
                    <RiskBadge level={w.risk_level} />
                    {w.is_mock && <span className="badge mock" style={{ marginLeft: 6 }}>Demo</span>}
                  </td>
                  <td>{{ pending: '待分析', processing: '分析中', completed: '已完成', failed: '失败' }[w.analysis_status]}</td>
                  <td>
                    <Link className="btn ghost light sm" to={`/teacher/warnings/${w.id}`}>
                      查看详情
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-title">安全事件（Honeypot 蜜罐触发）</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>关联用户</th>
                <th>IP</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_security_events?.length === 0 && (
                <tr>
                  <td colSpan="5" className="muted center">暂无安全事件</td>
                </tr>
              )}
              {data.recent_security_events?.map((e) => (
                <tr key={e.id}>
                  <td className="muted">{e.created_at}</td>
                  <td>
                    <span className="badge ana-failed">
                      {e.event_type === 'honeypot_field' ? '蜜罐字段' : '诱捕接口'}
                    </span>
                  </td>
                  <td>{e.username || '匿名'}</td>
                  <td className="mono">{e.ip || '—'}</td>
                  <td className="wrap muted">{e.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
