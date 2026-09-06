import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5175,
    proxy: {
      '/api': {
        // 127.0.0.1 直连：Windows 上 localhost 有 ~2s IPv6 回退延迟
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
