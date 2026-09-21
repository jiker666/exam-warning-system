import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import client, { fetchBlobUrl, request } from '../../api/client.js'
import { AnalysisBadge, RiskBadge } from '../../components/Badges.jsx'
import { examWindowText } from '../../utils/format.js'

/**
 * 在线考试页：
 * - PDF 试卷分页查看（上一页 / 下一页）
 * - getDisplayMedia + MediaRecorder 屏幕录制（混入麦克风音轨，供语音分析）
 * - 提交：停止录制 → Blob → FormData 上传 → 后端触发 AssemblyAI 分析
 */
export default function ExamPage() {
  const { examId } = useParams()
  const [exam, setExam] = useState(null)
  const [record, setRecord] = useState(null)
  const [pageUrls, setPageUrls] = useState([])
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const recorderRef = useRef(null)
  const displayStreamRef = useRef(null)
  const micRef = useRef(null)
  const chunksRef = useRef([])
  const [recording, setRecording] = useState(false)
  const [recSecs, setRecSecs] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [uploadPct, setUploadPct] = useState(null)
  const [honeypot, setHoneypot] = useState('') // 蜜罐隐藏字段：正常界面永远为空

  // ---- 加载考试 + 进入考试（创建考试记录）+ 加载试卷页面 ----
  useEffect(() => {
    let alive = true
    ;(async () => {
      try {
        const examData = await request({ url: `/exams/${examId}` })
        if (!alive) return
        setExam(examData)
        let rec = examData.my_record
        if (!rec && examData.is_open) {
          rec = await request({ method: 'post', url: '/records', data: { exam_id: Number(examId) } })
        }
        if (!alive) return
        setRecord(rec)

        const pagesData = await request({ url: `/exams/${examId}/pages` })
        if (!alive) return
        const urls = await Promise.all(pagesData.pages.map((p) => fetchBlobUrl(p.url)))
        if (alive) setPageUrls(urls)
      } catch (e) {
        if (alive) setError(e.message)
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
      setPageUrls((old) => {
        old.forEach((u) => URL.revokeObjectURL(u))
        return []
      })
    }
  }, [examId])

  // ---- 已提交但分析未完成时轮询分析状态 ----
  useEffect(() => {
    if (record?.status !== 'submitted') return
    if (!['pending', 'processing'].includes(record.analysis_status)) return
    const timer = setInterval(async () => {
      try {
        const data = await request({ url: `/records/${record.id}` })
        setRecord((old) => ({ ...old, ...data }))
      } catch {
        /* 网络抖动时继续轮询 */
      }
    }, 2000)
    return () => clearInterval(timer)
  }, [record?.id, record?.status, record?.analysis_status])

  // ---- 录制计时器 ----
  useEffect(() => {
    if (!recording) return
    const t = setInterval(() => setRecSecs((s) => s + 1), 1000)
    return () => clearInterval(t)
  }, [recording])

  // ---- 考试中关闭页面提醒 ----
  useEffect(() => {
    const h = (e) => {
      if (record?.status === 'in_progress') {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', h)
    return () => window.removeEventListener('beforeunload', h)
  }, [record?.status])

  const stopAllTracks = () => {
    displayStreamRef.current?.getTracks().forEach((t) => t.stop())
    micRef.current?.getTracks().forEach((t) => t.stop())
  }

  const startRecording = async () => {
    setError('')
    if (!navigator.mediaDevices?.getDisplayMedia) {
      setError('当前浏览器不支持屏幕录制（getDisplayMedia）。请使用 Chrome / Edge，并通过 localhost 或 HTTPS 访问。')
      return
    }
    try {
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 5 },
        audio: true,
      })
      displayStreamRef.current = displayStream
      let micStream = null
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      } catch {
        /* 学生拒绝麦克风时，仅录制屏幕共享声音 */
      }
      micRef.current = micStream

      const videoTracks = displayStream.getVideoTracks()
      const audioTracks = [
        ...displayStream.getAudioTracks(),
        ...(micStream ? micStream.getAudioTracks() : []),
      ]

      let mixed
      if (audioTracks.length > 1) {
        // 屏幕声音 + 麦克风混音，确保说话内容可被转录
        const ctx = new AudioContext()
        const dest = ctx.createMediaStreamDestination()
        audioTracks.forEach((t) => ctx.createMediaStreamSource(new MediaStream([t])).connect(dest))
        mixed = new MediaStream([...videoTracks, ...dest.stream.getAudioTracks()])
      } else {
        mixed = new MediaStream([...videoTracks, ...audioTracks])
      }

      const mimeType = ['video/webm;codecs=vp8,opus', 'video/webm'].find((t) =>
        MediaRecorder.isTypeSupported(t),
      )
      const recorder = new MediaRecorder(mixed, mimeType ? { mimeType } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = stopAllTracks
      // 学生点击浏览器自带"停止共享"按钮
      videoTracks[0]?.addEventListener('ended', () => setRecording(false))

      recorder.start(1000)
      recorderRef.current = recorder
      setRecSecs(0)
      setRecording(true)
    } catch (err) {
      setError(
        `无法开始屏幕录制：${err.message || err.name}。请选择"共享整个屏幕或浏览器标签页"，并允许录制权限。`,
      )
    }
  }

  const doSubmit = async () => {
    if (
      !window.confirm(
        '确定提交考试？\n提交后将停止录制并上传考试录像，系统将调用 AI 进行转录与风险分析。',
      )
    )
      return
    setSubmitting(true)
    setError('')
    setUploadPct(0)
    try {
      let blob = null
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        blob = await new Promise((resolve) => {
          recorderRef.current.onstop = () => {
            stopAllTracks()
            resolve(new Blob(chunksRef.current, { type: 'video/webm' }))
          }
          recorderRef.current.stop()
        })
      } else if (chunksRef.current.length > 0) {
        blob = new Blob(chunksRef.current, { type: 'video/webm' })
      }
      setRecording(false)

      const fd = new FormData()
      if (blob && blob.size > 0) fd.append('recording', blob, 'recording.webm')
      fd.append('contact_email_backup', honeypot) // 蜜罐字段（正常为空）

      const resp = await client.post(`/records/${record.id}/submit`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) setUploadPct(Math.max(1, Math.round((e.loaded / e.total) * 100)))
        },
      })
      setUploadPct(100)
      setRecord(resp.data.data)
    } catch (err) {
      setError(err.response?.data?.message || err.message)
      setSubmitting(false)
    }
  }

  if (loading) return <div className="muted">正在进入考试…</div>
  if (error && !exam) return (
    <div>
      <div className="alert error">{error}</div>
      <Link to="/student/exams" className="btn ghost light sm">← 返回考试列表</Link>
    </div>
  )
  if (!exam) return null

  const submitted = record?.status === 'submitted'
  const mm = String(Math.floor(recSecs / 60)).padStart(2, '0')
  const ss = String(recSecs % 60).padStart(2, '0')

  return (
    <div>
      {/* 蜜罐：正常学生永远不会看到/触碰的隐藏元素（反爬自动化检测） */}
      <input
        type="text"
        name="contact_email_backup"
        value={honeypot}
        onChange={(e) => setHoneypot(e.target.value)}
        style={{ display: 'none' }}
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
      />
      <a href="/api/admin/backup-keys" style={{ display: 'none' }} aria-hidden="true">.</a>

      <div className="exam-topbar">
        <div className="title">
          {exam.title}
          <div className="muted" style={{ fontWeight: 400, fontSize: 12 }}>
            {examWindowText(exam)} · 记录 #{record?.id}
          </div>
        </div>
        {submitted ? (
          <span className="badge st-submitted">已提交</span>
        ) : recording ? (
          <span className="rec-indicator"><span className="rec-dot" />正在录制 {mm}:{ss}</span>
        ) : (
          <span className="rec-idle">录制未开始</span>
        )}
        {!submitted && (
          <button className="btn danger" onClick={doSubmit} disabled={submitting}>
            {submitting ? '提交中…' : '提交考试'}
          </button>
        )}
      </div>

      {error && <div className="alert error">{error}</div>}

      {submitted ? (
        <SubmittedView record={record} />
      ) : (
        <div className="exam-layout">
          <div className="pdf-viewer">
            {pageUrls.length === 0 ? (
              <div className="muted">试卷加载中…</div>
            ) : (
              <>
                <img className="pdf-canvas" src={pageUrls[page - 1]} alt={`试卷第 ${page} 页`} />
                <div className="pdf-nav">
                  <button className="btn ghost light sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                    ← 上一页
                  </button>
                  <span>
                    第 {page} / {pageUrls.length} 页
                  </span>
                  <button
                    className="btn ghost light sm"
                    disabled={page >= pageUrls.length}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页 →
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="exam-side">
            <div className="card">
              <div className="card-title">考试录制</div>
              {recording ? (
                <>
                  <div className="alert warn" style={{ marginTop: 0 }}>
                    ● 正在录制考试过程（{mm}:{ss}）。请保持屏幕共享，直至提交考试。
                  </div>
                  <button className="btn ghost light" onClick={() => {
                    recorderRef.current?.stop()
                    setRecording(false)
                  }}>
                    暂停 / 停止共享
                  </button>
                  <div className="muted" style={{ marginTop: 8 }}>
                    注意：重新开始录制将覆盖之前已录制的片段，建议保持录制直至提交。
                  </div>
                </>
              ) : (
                <>
                  <div className="muted" style={{ marginBottom: 10 }}>
                    为进行考试过程 AI 分析，请点击下方按钮并<b>允许屏幕共享</b>
                    （同时会请求麦克风权限用于语音转录）。
                  </div>
                  <button className="btn" onClick={startRecording}>● 开始录制</button>
                </>
              )}
            </div>

            <div className="card">
              <div className="card-title">考试说明</div>
              <div className="muted" style={{ whiteSpace: 'pre-wrap' }}>
                {exam.description || '（无）'}
              </div>
            </div>

            <div className="card">
              <div className="card-title">提交状态</div>
              {submitting && (
                <>
                  <div className="muted">正在上传考试录像… {uploadPct}%</div>
                  <div className="progress"><div style={{ width: `${uploadPct || 1}%` }} /></div>
                </>
              )}
              <div className="muted">
                提交后系统将自动进行语音转录与异常行为分析，分析结果仅作为教师复核依据。
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SubmittedView({ record }) {
  return (
    <div className="card" style={{ maxWidth: 640, margin: '30px auto' }}>
      <div className="center" style={{ padding: '10px 0 20px' }}>
        <div style={{ fontSize: 42 }}>✅</div>
        <h2>考试已提交</h2>
        <p className="muted">提交时间：{record.submit_time}</p>
        {record.recording_url && (
          <p className="muted">考试录像已上传（{record.analysis_triggered ? 'AI 分析已触发' : ''}）</p>
        )}
      </div>

      <div className="kv">
        <span className="k">AI 分析状态</span>
        <span><AnalysisBadge status={record.analysis_status} isMock={record.is_mock_analysis} /></span>
      </div>
      {record.analysis_status === 'pending' && (
        <div className="alert info">排队等待 AI 分析，本页面会自动刷新结果…</div>
      )}
      {record.analysis_status === 'processing' && (
        <div className="alert info">
          <span className="spin" style={{ marginRight: 8 }} />
          AssemblyAI 正在转录考试音频，并进行关键词风险分析…
        </div>
      )}
      {record.analysis_status === 'completed' && (
        <>
          <div className="kv">
            <span className="k">风险评分</span>
            <span>
              <b style={{ fontSize: 16 }}>{record.risk_score}</b> 分 <RiskBadge level={record.risk_level} />
            </span>
          </div>
          <div className="kv">
            <span className="k">分析来源</span>
            <span className="muted">{record.analysis_note || '—'}</span>
          </div>
          <div className="alert warn">
            AI 分析结果仅作为考试行为预警与教师复核依据，不代表最终判定。
            {record.is_mock_analysis && ' 当前为 Demo 模拟分析结果（Mock Result）。'}
          </div>
        </>
      )}
      {record.analysis_status === 'failed' && (
        <div className="alert error">分析失败：{record.analysis_note || '未知原因'}，请联系教师处理。</div>
      )}

      <div className="center" style={{ marginTop: 16 }}>
        <Link to="/student/exams" className="btn">← 返回考试列表</Link>
      </div>
    </div>
  )
}
