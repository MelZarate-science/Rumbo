import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/app/',
  plugins: [react()],
  server: {
    proxy: {
      '/perfiles': 'http://localhost:8080',
      '/empresas': 'http://localhost:8080',
      '/puestos': 'http://localhost:8080',
      '/matches': 'http://localhost:8080',
      '/auth': 'http://localhost:8080',
    },
  },
})
