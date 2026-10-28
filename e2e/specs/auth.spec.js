import { test, expect } from '@playwright/test'
import { ADMIN, STUDENT, loginThroughUi, mockApi, seedLogin } from './mock-api.js'

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear())
})

test('未登录访问业务页面会跳转到登录页', async ({ page }) => {
  await mockApi(page)
  await page.goto('/manager/home')
  await expect(page).toHaveURL(/\/login$/)
})

test('学生登录后进入首页，只看到学生菜单', async ({ page }) => {
  await mockApi(page, { user: STUDENT })
  await loginThroughUi(page, STUDENT)

  await expect(page.getByText('E2E学生')).toBeVisible()
  await expect(page.locator('.el-menu').getByText('实验室列表')).toBeVisible()
  await expect(page.locator('.el-menu').getByText('我的预约')).toBeVisible()
  await expect(page.locator('.el-menu').getByText('用户管理')).toHaveCount(0)
  await expect(page.locator('.el-menu').getByText('预约审核')).toHaveCount(0)
})

test('管理员登录后能看到管理菜单', async ({ page }) => {
  await mockApi(page, { user: ADMIN })
  await loginThroughUi(page, ADMIN)

  await expect(page.locator('.el-menu').getByText('用户管理')).toBeVisible()
  await expect(page.locator('.el-menu').getByText('预约审核')).toBeVisible()
})

test('学生直接输入管理页 URL 应被路由守卫拦截', async ({ page }) => {
  // 已知缺陷：当前路由守卫只判断 token 是否存在，不判断角色。
  test.fail(true, 'known bug: 前端路由没有角色守卫，学生可直接打开 /manager/user')

  await mockApi(page, { user: STUDENT })
  await seedLogin(page, STUDENT)
  await page.goto('/manager/user')

  await expect(page).toHaveURL(/\/login$/)
})
