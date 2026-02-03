import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/status': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/start': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/stop': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/resume': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/messages': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/memory': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/agents': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/audio': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/filter': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
})
