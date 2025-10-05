import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || '')
  },
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.BACKEND_API_URL || 'http://localhost:64451',
        changeOrigin: true,
        secure: false,
        // 支持多种代理目标
        router: (req) => {
          const host = req.headers.host?.split(':')[0]
          if (host && /^\d+\.\d+\.\d+\.\d+$/.test(host)) {
            // 如果是IP访问，使用相同的IP
            return `http://${host}:64451`
          }
          // 默认使用localhost
          return 'http://localhost:64451'
        }
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  base: './',
})