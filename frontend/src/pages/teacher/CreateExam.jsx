import { useNavigate } from 'react-router-dom'
import ExamForm from '../../components/ExamForm.jsx'

export default function CreateExam() {
  const navigate = useNavigate()
  return (
    <div style={{ maxWidth: 720 }}>
      <h1 className="page-title">创建考试</h1>
      <p className="page-sub">上传 PDF 试卷后，系统将自动逐页解析为图片供学生在浏览器中作答查看</p>
      <div className="card">
        <ExamForm
          submitText="创建考试（保存为草稿）"
          onSubmit={() => navigate('/teacher/exams')}
        />
      </div>
    </div>
  )
}
