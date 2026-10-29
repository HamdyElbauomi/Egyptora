import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The backend runs on :8000 (uvicorn). In dev, /api and /uploads are proxied to it,
// so the app and the API share one origin and no CORS setup is needed.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/uploads': 'http://localhost:8000',
    },
  },
})
