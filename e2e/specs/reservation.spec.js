import { test, expect } from '@playwright/test'
import { LABS, STUDENT, mockApi, seedLogin } from './mock-api.js'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear())
})

test('学生从实验室列表提交预约', async ({ page }) => {
  const captured = await mockApi(page, { user: STUDENT, labs: LABS })
  await seedLogin(page, STUDENT)
  await page.goto('/manager/lablist')

  await expect(page.getByText('E2E实验室')).toBeVisible()

  const card = page.locator('.el-card').filter({ hasText: 'E2E实验室' }).first()
  await card.getByRole('button', { name: '预约' }).click()

  const dialog = page.locator('.el-dialog').filter({ hasText: '预约' })
  await expect(dialog).toBeVisible()

  // 打开日期面板，选一个可用日期（不依赖具体系统日期）
  await dialog.getByPlaceholder('请选择日期').click()
  await page.locator('.el-date-table td.available').last().click()
  await dialog.getByRole('button', { name: '确定' }).click()

  await expect(page.getByText('预约已提交，请等待审核')).toBeVisible()

  const created = captured.requests.find(
    (item) => item.method === 'POST' && item.path === '/api/reservation'
  )
  expect(created).toBeTruthy()
  expect(created.body.lab_id).toBe(1)
  expect(created.body.date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  expect(created.body.start_time).toBe('09:00')
  expect(created.body.end_time).toBe('18:00')
})

test('待审核预约可以取消', async ({ page }) => {
  const reservation = {
    id: 10,
    user_id: STUDENT.id,
    user_name: STUDENT.name,
    lab_id: 1,
    lab_name: 'E2E实验室',
    equipment_id: null,
    equipment_name: null,
    type: '实验室',
    date: '2026-10-28',
    start_time: '09:00',
    end_time: '10:00',
    remark: '',
    status: 0
  }
  const captured = await mockApi(page, {
    user: STUDENT,
    labs: LABS,
    reservations: [reservation]
  })
  await seedLogin(page, STUDENT)
  await page.goto('/manager/my-reservation')

  await expect(page.getByText('E2E实验室')).toBeVisible()
  await page.getByRole('button', { name: '取消' }).click()

  const confirm = page.locator('.el-message-box')
  await confirm.getByRole('button', { name: '确定' }).click()

  await expect(page.getByText('取消预约成功')).toBeVisible()
  expect(
    captured.requests.some(
      (item) => item.method === 'PUT' && item.path === '/api/reservation/10/cancel'
    )
  ).toBeTruthy()
})
