import { Navigate } from 'react-router-dom'
import { useAuth } from '../AuthContext.jsx'

/** 路由守卫：未登录跳登录页；角色不匹配跳转对应首页 */
export default function ProtectedRoute({ roles, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} replace />
  }
  return children
}
