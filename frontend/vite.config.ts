import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/predict': 'http://127.0.0.1:5000',
      '/predict-multi': 'http://127.0.0.1:5000',
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
