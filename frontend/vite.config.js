import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 后端 Flask 默认运行在 5001（macOS 5000 被 AirPlay 占用）
// 本地 5173 被其他项目占用，前端开发服务器使用 5174
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/api': { target: 'http://localhost:5001', changeOrigin: true },
    },
  },
})
