import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext.jsx'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!username || !password) {
      setError('请输入用户名和密码')
      return
    }
    setError('')
    setLoading(true)
    try {
      const user = await login(username.trim(), password)
      navigate(user.role === 'teacher' ? '/teacher' : '/student', { replace: true })
    } catch (err) {
      setError(err.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="brand-logo">✳</div>
        </div>
        <h1 className="login-title">考试预警系统</h1>
        <div className="login-sub">基于 AssemblyAI 的在线考试风险预警平台</div>

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={onSubmit}>
          <div className="form-item">
            <label>用户名</label>
            <input
              type="text"
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-item">
            <label>密码</label>
            <input
              type="password"
              placeholder="请输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button className="btn" style={{ width: '100%' }} disabled={loading}>
            {loading ? '登录中…' : '登 录'}
          </button>
        </form>

        <div className="login-demo">
          <b>本地演示账号</b>（由 <code>backend/seed.py</code> 创建）
          <br />
          教师：<code>teacher / 123456</code>
          <br />
          学生：<code>student01 / 123456</code>
        </div>
      </div>
    </div>
  )
}
