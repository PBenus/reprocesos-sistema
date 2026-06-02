import { useState, useEffect, useCallback } from 'react'
import { login as apiLogin, getMe } from '../api/auth'

const TOKEN_KEY = 'reprocesos_token'
const USER_KEY  = 'reprocesos_user'

export function useAuth() {
  const [user, setUser]         = useState(null)
  const [isLoading, setLoading] = useState(true)

  // On mount: restore session from localStorage
  useEffect(() => {
    const token    = localStorage.getItem(TOKEN_KEY)
    const cached   = localStorage.getItem(USER_KEY)
    if (token && cached) {
      try {
        setUser(JSON.parse(cached))
      } catch { /* ignore */ }
      // Verify token is still valid
      getMe()
        .then((me) => { setUser(me); localStorage.setItem(USER_KEY, JSON.stringify(me)) })
        .catch(() => { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); setUser(null) })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (usuario, password) => {
    const data = await apiLogin(usuario, password)
    localStorage.setItem(TOKEN_KEY, data.access_token)
    const me = { id: data.id, nombre: data.nombre, rol: data.rol, usuario }
    localStorage.setItem(USER_KEY, JSON.stringify(me))
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
    window.location.href = '/login'
  }, [])

  return { user, isLoading, isAuthenticated: !!user, login, logout }
}
