import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // permite acceso desde la red local en desarrollo
    // Proxy solo activo en desarrollo. En producción (Vercel),
    // el frontend usa VITE_API_URL del .env.production → tunnel de Cloudflare
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

