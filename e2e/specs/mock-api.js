/**
 * 前端 E2E 共用的接口模拟。
 *
 * 前端 axios/fetch 的 baseURL 是 http://127.0.0.1:8000，和页面不同源，
 * 因此这里统一处理 OPTIONS 预检并补齐 CORS 头。
 */

export const STUDENT = {
  id: 1,
  username: 'e2e_student',
  name: 'E2E学生',
  role: 'student',
  status: 1,
  email: null,
  phone: null,
  avatar: null
}

export const ADMIN = {
  ...STUDENT,
  id: 2,
  username: 'e2e_admin',
  name: 'E2E管理员',
  role: 'admin'
}

export const LABS = [
  {
    id: 1,
    name: 'E2E实验室',
    location: '综合实验楼101',
    capacity: 30,
    open_time: '08:00',
    close_time: '18:00',
    description: '用于端到端测试',
    img: null,
    status: 1
  }
]

const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET,POST,PUT,DELETE,OPTIONS',
  'access-control-allow-headers': '*'
}

function json(route, body, status = 200) {
  return route.fulfill({
    status,
    headers: { ...CORS, 'content-type': 'application/json' },
    body: JSON.stringify(body)
  })
}

export async function mockApi(page, options = {}) {
  const user = options.user || STUDENT
  const labs = options.labs || LABS
  const reservations = options.reservations || []
  const captured = options.captured || { requests: [] }

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const method = request.method()
    const url = new URL(request.url())
    const path = url.pathname

    if (method === 'OPTIONS') {
      return route.fulfill({ status: 204, headers: CORS })
    }

    if (path === '/api/auth/login') {
      return json(route, {
        code: 200,
        message: '登录成功',
        data: { token: 'e2e-token', user }
      })
    }

    if (path === '/api/lab/list') {
      return json(route, {
        code: 200,
        message: '请求成功',
        data: { list: labs, total: labs.length }
      })
    }

    if (path === '/api/reservation/list') {
      return json(route, {
        code: 200,
        message: '请求成功',
        data: { list: reservations, total: reservations.length }
      })
    }

    if (path === '/api/reservation' && method === 'POST') {
      captured.requests.push({ method, path, body: request.postDataJSON() })
      return json(route, { code: 200, message: '请求成功', data: null })
    }

    if (/^\/api\/reservation\/\d+\/cancel$/.test(path) && method === 'PUT') {
      captured.requests.push({ method, path })
      return json(route, { code: 200, message: '取消预约成功', data: null })
    }

    if (path === '/api/user/list') {
      return json(route, {
        code: user.role === 'admin' ? 200 : 403,
        message: user.role === 'admin' ? '请求成功' : '无权限访问',
        data: { list: [], total: 0 }
      })
    }

    if (path === '/api/ai/chat/stream') {
      const body =
        'data: {"type":"status","message":"正在思考..."}\n\n' +
        'data: {"type":"token","content":"你可以先选择实验室，再提交预约。"}\n\n' +
        'data: {"type":"done"}\n\n'
      return route.fulfill({
        status: 200,
        headers: { ...CORS, 'content-type': 'text/event-stream' },
        body
      })
    }

    return json(route, { code: 200, message: '请求成功', data: null })
  })

  return captured
}

/** 直接写入登录态，跳过登录表单。 */
export async function seedLogin(page, user = STUDENT) {
  await page.addInitScript(
    ({ token, userInfo }) => {
      localStorage.setItem('token', token)
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
    },
    { token: 'e2e-token', userInfo: user }
  )
}

/** 通过登录页真实走一遍表单。 */
export async function loginThroughUi(page, user = STUDENT) {
  await page.goto('/login')
  await page.getByPlaceholder('请输入账号').fill(user.username)
  await page.getByPlaceholder('请输入密码').fill('Test@123456')
  await page.locator('.submit-btn').click()
  await page.waitForURL('**/manager/home')
}
