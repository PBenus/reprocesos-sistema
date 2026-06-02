import client from './client'

export const login = (usuario, password) =>
  client.post('/auth/login', { usuario, password }).then((r) => r.data)

export const getMe = () =>
  client.get('/auth/me').then((r) => r.data)

export const register = (data) =>
  client.post('/auth/register', data).then((r) => r.data)
