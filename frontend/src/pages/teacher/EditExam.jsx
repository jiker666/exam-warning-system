import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ExamForm from '../../components/ExamForm.jsx'
import { request } from '../../api/client.js'

export default function EditExam() {
  const { examId } = useParams()
  const navigate = useNavigate()
  const [exam, setExam] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    request({ url: `/exams/${examId}` }).then(setExam).catch((e) => setError(e.message))
  }, [examId])

  return (
    <div style={{ maxWidth: 720 }}>
      <h1 className="page-title">编辑考试</h1>
      <p className="page-sub">修改考试基本信息，或替换 PDF 试卷（重新上传会重新解析页面）</p>
      <div className="card">
        {error && <div className="alert error">{error}</div>}
        {!exam ? (
          <div className="muted">加载中…</div>
        ) : (
          <ExamForm initial={exam} submitText="保存修改" onSubmit={() => navigate('/teacher/exams')} />
        )}
      </div>
    </div>
  )
}
