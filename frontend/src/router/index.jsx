import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute.jsx'
import Layout from '../components/Layout.jsx'
import TeacherDashboard from '../pages/teacher/TeacherDashboard.jsx'
import ExamManagement from '../pages/teacher/ExamManagement.jsx'
import CreateExam from '../pages/teacher/CreateExam.jsx'
import EditExam from '../pages/teacher/EditExam.jsx'
import StudentRecords from '../pages/teacher/StudentRecords.jsx'
import WarningCenter from '../pages/teacher/WarningCenter.jsx'
import WarningDetail from '../pages/teacher/WarningDetail.jsx'
import ScoreManagement from '../pages/teacher/ScoreManagement.jsx'
import StudentHome from '../pages/student/StudentHome.jsx'
import ExamList from '../pages/student/ExamList.jsx'
import ExamPage from '../pages/student/ExamPage.jsx'

function Home() {
  const role = JSON.parse(localStorage.getItem('user') || 'null')?.role
  return <Navigate to={role === 'teacher' ? '/teacher' : '/student'} replace />
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route
        path="/login"
        element={<Navigate to="/" replace />}
      />
      {/* 教师端 */}
      <Route
        element={
          <ProtectedRoute roles={['teacher']}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/teacher" element={<TeacherDashboard />} />
        <Route path="/teacher/exams" element={<ExamManagement />} />
        <Route path="/teacher/exams/create" element={<CreateExam />} />
        <Route path="/teacher/exams/:examId/edit" element={<EditExam />} />
        <Route path="/teacher/records" element={<StudentRecords />} />
        <Route path="/teacher/warnings" element={<WarningCenter />} />
        <Route path="/teacher/warnings/:warningId" element={<WarningDetail />} />
        <Route path="/teacher/scores" element={<ScoreManagement />} />
      </Route>
      {/* 学生端 */}
      <Route
        element={
          <ProtectedRoute roles={['student']}>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/student" element={<StudentHome />} />
        <Route path="/student/exams" element={<ExamList />} />
        <Route path="/student/exam/:examId" element={<ExamPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
