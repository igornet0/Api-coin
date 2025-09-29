import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import dotenv from 'dotenv'
import path from 'path'

// Определяем режим и загружаем соответствующий env файл
const mode = process.env.NODE_ENV || 'development'
const envFile = mode === 'production' ? '../settings/prod.env' : '../settings/dev.env'

// Загружаем переменные окружения
dotenv.config({ path: path.resolve(__dirname, envFile) })

// Извлекаем нужные переменные
const frontendHost = process.env.APP__FRONTEND_HOST || 'localhost'
const frontendPort = parseInt(process.env.APP__FRONTEND_PORT || '3000')
const apiHost = process.env.APP__HOST || 'localhost'
const apiPort = parseInt(process.env.APP__PORT || '8080')

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: frontendHost,
    port: frontendPort,
    proxy: {
      '/api': {
        target: `http://${apiHost}:${apiPort}`,
        changeOrigin: true,
        secure: false
      }
    }
  },
  define: {
    // Делаем переменные доступными в клиентском коде
    __API_URL__: JSON.stringify(`http://${apiHost}:${apiPort}`)
  }
})
