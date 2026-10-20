import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5174,
    strictPort: true, // 端口被占就直接报错，不要偷偷跳到 5175
    proxy:{
      '/api':{
        target:'http://127.0.0.1:8000',
        changeOrigin:true
      },
      '/uploads':{
        target:'http://127.0.0.1:8000',
        changeOrigin:true
      }
    }
  },
})
