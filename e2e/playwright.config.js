import { defineConfig, devices } from '@playwright/test'

/**
 * 默认只启动前端，接口全部用 page.route 模拟，所以不依赖后端和数据库。
 * 想跑真实后端冒烟：先启动 backend，再设置 E2E_REAL=1 和 E2E_USERNAME/E2E_PASSWORD。
 */
export default defineConfig({
  testDir: './specs',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:5174',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    cwd: '../frontend',
    url: 'http://127.0.0.1:5174',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
})
