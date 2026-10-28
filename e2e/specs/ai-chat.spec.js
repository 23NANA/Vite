import { test, expect } from '@playwright/test'
import { STUDENT, mockApi, seedLogin } from './mock-api.js'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear())
})

test('AI 助手以流式方式渲染回答', async ({ page }) => {
  await mockApi(page, { user: STUDENT })
  await seedLogin(page, STUDENT)
  await page.goto('/manager/ai-chat')

  await page
    .getByPlaceholder('问问实验室怎么预约、开放时间...')
    .fill('怎么预约实验室？')
  await page.locator('.send-btn').click()

  await expect(
    page.locator('.msg-content').filter({ hasText: '你可以先选择实验室，再提交预约。' })
  ).toBeVisible()
})

test('AI 返回的 Markdown 会被消毒，不能执行脚本', async ({ page }) => {
  await mockApi(page, { user: STUDENT })
  // 后注册的 route 优先匹配，所以这里覆盖 mockApi 里的默认流式响应
  await page.route('**/api/ai/chat/stream', (route) =>
    route.fulfill({
      status: 200,
      headers: {
        'access-control-allow-origin': '*',
        'content-type': 'text/event-stream'
      },
      body:
        'data: {"type":"token","content":"<img src=x onerror=\\"window.__xss=1\\">**安全**"}\n\n' +
        'data: {"type":"done"}\n\n'
    })
  )
  await seedLogin(page, STUDENT)
  await page.goto('/manager/ai-chat')

  await page
    .getByPlaceholder('问问实验室怎么预约、开放时间...')
    .fill('测试 XSS')
  await page.locator('.send-btn').click()

  await expect(page.locator('.msg-content').filter({ hasText: '安全' })).toBeVisible()
  const executed = await page.evaluate(() => Boolean(window.__xss))
  expect(executed).toBe(false)
})
