import client from './client'

export const uploadFoto = async (file) => {
  const form = new FormData()
  form.append('file', file)
  const res = await client.post('/fotos/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data // { url: '...' }
}
