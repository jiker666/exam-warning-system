import { createContext, useContext, useMemo, useState } from 'react'
import { request } from './api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user') || 'null')
    } catch {
      return null
    }
  })

  const value = useMemo(
    () => ({
      user,
      async login(username, password) {
        const data = await request({ method: 'post', url: '/auth/login', data: { username, password } })
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        setUser(data.user)
        return data.user
      },
      logout() {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setUser(null)
      },
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
