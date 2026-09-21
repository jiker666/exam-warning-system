import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext.jsx'

const TEACHER_NAV = [
  { to: '/teacher', label: '首页 Dashboard', end: true },
  { to: '/teacher/exams', label: '考试管理' },
  { to: '/teacher/exams/create', label: '创建考试' },
  { to: '/teacher/records', label: '学生考试记录' },
  { to: '/teacher/warnings', label: 'AI 风险预警中心' },
  { to: '/teacher/scores', label: '成绩管理' },
]

const STUDENT_NAV = [
  { to: '/student', label: '首页', end: true },
  { to: '/student/exams', label: '考试列表' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const nav = user?.role === 'teacher' ? TEACHER_NAV : STUDENT_NAV

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">✳</div>
          <div>
            <div className="brand-title">考试预警系统</div>
            <div className="brand-sub">基于 AssemblyAI</div>
          </div>
        </div>
        <nav className="nav">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip">
            <span className={`role-dot role-${user?.role}`} />
            <span>{user?.username}</span>
            <span className="role-name">{user?.role === 'teacher' ? '教师' : '学生'}</span>
          </div>
          <button
            className="btn ghost sm"
            onClick={() => {
              logout()
              navigate('/login')
            }}
          >
            退出登录
          </button>
        </div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
