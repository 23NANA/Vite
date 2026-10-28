import { test, expect } from '@playwright/test'

/**
 * 真实后端冒烟：默认跳过。
 *
 *   E2E_REAL=1 E2E_USERNAME=xxx E2E_PASSWORD=xxx npx playwright test real-backend
 */
test.skip(!process.env.E2E_REAL, '需要真实后端，设置 E2E_REAL=1 后运行')

test('真实后端登录并打开首页', async ({ page }) => {
  await page.goto('/login')
  await page.getByPlaceholder('请输入账号').fill(process.env.E2E_USERNAME || '')
  await page.getByPlaceholder('请输入密码').fill(process.env.E2E_PASSWORD || '')
  await page.locator('.submit-btn').click()

  await expect(page).toHaveURL(/\/manager\/home/)
  await expect(page.getByText('智能实验室预约系统').first()).toBeVisible()
})
