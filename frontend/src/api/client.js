import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 segundos — evita Network Error en operaciones lentas (cierre + Supabase)
})

// Attach JWT token on every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('reprocesos_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login on 401
client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('reprocesos_token')
      localStorage.removeItem('reprocesos_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
