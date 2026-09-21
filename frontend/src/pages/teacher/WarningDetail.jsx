import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchBlobUrl, request } from '../../api/client.js'
import { RiskBadge } from '../../components/Badges.jsx'
import { examWindowText } from '../../utils/format.js'

export default function WarningDetail() {
  const { warningId } = useParams()
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [reviewNote, setReviewNote] = useState('')
  const [videoUrl, setVideoUrl] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () =>
    request({ url: `/warnings/${warningId}` })
      .then((d) => {
        setDetail(d)
        setReviewNote(d.review_note || '')
        if (d.record?.recording_url) {
          fetchBlobUrl(d.record.recording_url).then(setVideoUrl).catch(() => setVideoUrl(''))
        }
      })
      .catch((e) => setError(e.message))
  useEffect(load, [warningId])

  const saveReview = async () => {
    if (!reviewNote.trim()) return setMsg('复核意见不能为空')
    setBusy(true)
    try {
      await request({
        method: 'post',
        url: `/warnings/${warningId}/review`,
        data: { review_note: reviewNote.trim() },
      })
      setMsg('复核意见已保存')
      load()
    } catch (e) {
      setMsg(e.message)
    } finally {
      setBusy(false)
    }
  }

  const reanalyze = async () => {
    setBusy(true)
    setMsg('已重新触发 AI 分析，请稍后刷新查看结果…')
    try {
      await request({ method: 'post', url: `/records/${detail.record.id}/analyze` })
    } catch (e) {
      setMsg(e.message)
    } finally {
      setBusy(false)
    }
  }

  if (error) return <div className="alert error">{error}</div>
  if (!detail) return <div className="muted">加载中…</div>

  const rec = detail.record
  const student = detail.student
  const exam = detail.exam

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <Link to="/teacher/warnings" className="btn ghost light sm">← 返回预警中心</Link>
        <h1 className="page-title mt0" style={{ flex: 1 }}>
          预警详情 #{detail.id}
        </h1>
        <RiskBadge level={detail.risk_level} />
        {detail.is_mock && <span className="badge mock">⚠ Demo 模拟分析（非真实 AI 结果）</span>}
      </div>

      {msg && <div className="alert info">{msg}</div>}

      <div className="detail-grid" style={{ marginBottom: 18 }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">学生信息</div>
          <div className="kv"><span className="k">用户名</span><span>{student.username}</span></div>
          <div className="kv"><span className="k">角色</span><span>学生</span></div>
          <div className="kv"><span className="k">记录 ID</span><span>#{rec.id}</span></div>
          <div className="kv"><span className="k">提交时间</span><span>{rec.submit_time || '—'}</span></div>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-title">考试信息</div>
          <div className="kv"><span className="k">考试</span><span>{exam.title}</span></div>
          <div className="kv"><span className="k">考试时间</span><span>{examWindowText(exam)}</span></div>
          <div className="kv"><span className="k">开始作答</span><span>{rec.start_time || '—'}</span></div>
          <div className="kv"><span className="k">成绩</span><span>{rec.score ?? '未录入'}</span></div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">风险评分</div>
        <div className="risk-score-big" style={{ marginBottom: 14 }}>
          <div className={`score-circle ${detail.risk_level}`}>
            <div className="num">{detail.risk_score}</div>
            <div className="cap">风险分</div>
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>
              风险等级：<RiskBadge level={detail.risk_level} />
            </div>
            <div className="muted">{detail.warning_content}</div>
            <div className="muted" style={{ marginTop: 4 }}>
              分析状态：{rec.analysis_note || '—'}
            </div>
          </div>
        </div>
        <div style={{ marginTop: 10 }}>
          <b style={{ fontSize: 13 }}>命中关键词</b>
          <div style={{ marginTop: 8 }}>
            {detail.hit_keywords.length === 0 && <span className="muted">未命中任何关键词</span>}
            {detail.hit_keywords.map((h) => (
              <span key={h.keyword} className="kw-chip">
                {h.keyword} <b>×{h.count}</b>（{h.category_label}，+{h.points} 分）
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">AI 转录结果 {detail.is_mock && <span className="badge mock">Mock Result</span>}</div>
        <div className="transcript-box">{detail.transcript || '（无转录内容）'}</div>
      </div>

      <div className="card">
        <div className="card-title">考试录像</div>
        {videoUrl ? (
          <video className="rec-video" src={videoUrl} controls />
        ) : (
          <div className="muted">该记录没有考试录像（种子演示数据未上传录像文件）</div>
        )}
      </div>

      <div className="card">
        <div className="card-title">教师复核意见</div>
        {detail.reviewed && detail.review_note && (
          <div className="alert ok">
            <b>已复核：</b>{detail.review_note}
          </div>
        )}
        <textarea
          placeholder="填写复核意见，例如：已人工回看录像并与学生核实，确认为同桌声音 / 确认存在违纪行为，按考试纪律处理…"
          value={reviewNote}
          onChange={(e) => setReviewNote(e.target.value)}
        />
        <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
          <button className="btn" onClick={saveReview} disabled={busy}>保存复核意见</button>
          <button className="btn ghost light" onClick={reanalyze} disabled={busy}>重新 AI 分析</button>
        </div>
        <div className="muted" style={{ marginTop: 8 }}>
          * 风险结果仅作为考试行为预警 / 教师复核依据，不直接判定学生作弊
        </div>
      </div>
    </div>
  )
}
