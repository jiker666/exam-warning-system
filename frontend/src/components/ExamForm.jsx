import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client.js'

/** 创建 / 编辑考试共用的表单组件 */
export default function ExamForm({ initial, submitText, onSubmit }) {
  const [form, setForm] = useState({
    title: initial?.title || '',
    description: initial?.description || '',
    start_time: initial?.start_time ? initial.start_time.replace(' ', 'T') : '',
    end_time: initial?.end_time ? initial.end_time.replace(' ', 'T') : '',
  })
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return setError('请填写考试标题')
    if (!file && !initial?.pdf_path) return setError('请上传 PDF 试卷')
    if (file && !file.name.toLowerCase().endsWith('.pdf')) return setError('试卷仅支持 PDF 格式')

    setError('')
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('title', form.title.trim())
      fd.append('description', form.description.trim())
      if (form.start_time) fd.append('start_time', form.start_time)
      if (form.end_time) fd.append('end_time', form.end_time)
      if (file) fd.append('pdf', file)
      const resp = await client({
        method: initial ? 'put' : 'post',
        url: initial ? `/exams/${initial.id}` : '/exams',
        data: fd,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onSubmit(resp.data.data)
    } catch (err) {
      setError(err.response?.data?.message || err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit}>
      <div className="form-item">
        <label>考试标题 *</label>
        <input type="text" placeholder="例如：2026 春季《计算机导论》期中考试" value={form.title} onChange={set('title')} />
      </div>
      <div className="form-item">
        <label>考试说明</label>
        <textarea placeholder="考试注意事项、题型说明等（可选）" value={form.description} onChange={set('description')} />
      </div>
      <div className="form-row">
        <div className="form-item">
          <label>开始时间 <span className="hint">（可选，留空表示不限）</span></label>
          <input type="datetime-local" value={form.start_time} onChange={set('start_time')} />
        </div>
        <div className="form-item">
          <label>结束时间 <span className="hint">（可选）</span></label>
          <input type="datetime-local" value={form.end_time} onChange={set('end_time')} />
        </div>
      </div>
      <div className="form-item">
        <label>
          PDF 试卷 * {!initial?.pdf_path ? '' : <span className="hint">（已有试卷，重新上传将替换并重新解析）</span>}
        </label>
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {initial?.pdf_path && !file && (
          <div className="muted" style={{ marginTop: 6 }}>
            当前试卷：{initial.page_count} 页（PDF 已解析为图片，学生端分页展示）
          </div>
        )}
        {file && <div className="muted" style={{ marginTop: 6 }}>已选择：{file.name}（{(file.size / 1024 / 1024).toFixed(2)} MB）</div>}
      </div>

      {error && <div className="alert error">{error}</div>}
      <button className="btn" disabled={busy}>{busy ? '提交中…' : submitText}</button>
    </form>
  )
}
