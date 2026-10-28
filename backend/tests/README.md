# 后端自动化测试

## 运行

```bash
cd backend
./.venv/Scripts/python.exe -m pip install -r requirements-test.txt
./.venv/Scripts/python.exe -m pytest
```

测试会自动：

1. 读取 `backend/.env` 里的 `DATABASE_URL`，把库名替换成 `lab_agent_test`；
2. 如果测试库不存在，自动创建；
3. 强制使用测试 JWT 密钥和假 LLM 配置，不会调用真实大模型；
4. 每个用例前后清空测试库。

也可以用 `TEST_DATABASE_URL` 显式指定测试库：

```bash
TEST_DATABASE_URL="mysql+pymysql://root:root@127.0.0.1:3306/lab_agent_test?charset=utf8mb4" \
  ./.venv/Scripts/python.exe -m pytest
```

> 不会碰 `lab_agent` 开发库。应用在 import 时执行 `create_all`，所以测试库必须有建表权限。

## 目录

```
tests/
  conftest.py          测试库、TestClient、用户/实验室/设备 fixtures
  factories.py         直接落库的数据工厂
  helpers.py           登录、统一断言
  api/                 接口级用例（主力）
  services/            服务层边界用例
  ai/                  Agent 工具、SSE 契约、RAG 黄金集
```

## xfail 的含义

测试套件里有 18 条 `xfail`，它们断言的是**正确行为**，但当前实现不满足，对应已知缺陷。修好后会自动变成 XPASS，不会阻塞 CI。

覆盖的已知缺陷：

- 已通过预约不能取消（与知识库冲突）
- 设备预约不占用实验室时段（与知识库冲突）
- 预约日期/时间无格式校验、字符串比较
- 设备可跨实验室预约
- 并发重复预约
- 过期扫描任务 `changed` 未初始化
- 删除被引用数据返回 500
- `UserUpdateRequest` 重复定义导致角色/状态被丢弃
- 上传接口无鉴权
- 实验室 `status=0` 过滤失效
- 已删除用户的 token 返回 500
- 注册允许空用户名/密码

## AI 测试

默认不加载 embedding 模型。Agent 工具测试通过 monkeypatch 绕开知识库；SSE 测试使用假 Agent。

跑真实 RAG 检索（会加载/下载 `BAAI/bge-small-zh-v1.5`）：

```bash
RUN_RAG_TESTS=1 ./.venv/Scripts/python.exe -m pytest tests/ai/test_rag_golden.py -v
```

## 前端 E2E

```bash
cd e2e
npm install
npx playwright install chromium
npm test
```

E2E 默认只启动前端，所有接口用 `page.route` 模拟，不依赖后端。真实后端冒烟：

```bash
E2E_REAL=1 E2E_USERNAME=xxx E2E_PASSWORD=xxx npm test -- real-backend
```
