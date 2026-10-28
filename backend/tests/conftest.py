"""测试入口：先把环境切到独立测试库，再导入应用。

注意顺序：app.config 在 import 时就会读取环境变量，app.main 在 import 时就会
执行 Base.metadata.create_all。所以所有环境覆盖必须放在 app.* 导入之前。
"""

from __future__ import annotations

import os
from pathlib import Path

import pymysql
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"
TEST_DB_NAME = "lab_agent_test"
DEFAULT_PASSWORD = "Test@123456"


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _build_test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit

    base = os.environ.get("DATABASE_URL") or _read_env_file(ENV_FILE).get("DATABASE_URL")
    if not base:
        raise RuntimeError(
            "未找到数据库配置。请设置 TEST_DATABASE_URL，或在 backend/.env 中配置 DATABASE_URL。"
        )
    return make_url(base).set(database=TEST_DB_NAME).render_as_string(hide_password=False)


def _ensure_database(url_str: str) -> None:
    url = make_url(url_str)
    conn = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=url.port or 3306,
        user=url.username,
        password=url.password or "",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()


TEST_DATABASE_URL = _build_test_database_url()
_ensure_database(TEST_DATABASE_URL)

# 强制覆盖，避免测试误连开发库、误用真实大模型或开发 JWT 密钥。
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_EXPIRE_HOURS"] = "24"
os.environ["LLM_API_KEY"] = "test-key"
os.environ["LLM_MODEL"] = "test-model"
os.environ["LLM_BASE_URL"] = "http://127.0.0.1:9/v1"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from tests import factories  # noqa: E402
from tests.helpers import login  # noqa: E402


def _truncate_all() -> None:
    """每个用例前后清库，保证用例互不影响。"""
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


@pytest.fixture(autouse=True)
def clean_database():
    _truncate_all()
    yield
    _truncate_all()


@pytest.fixture()
def client():
    # 不使用 with TestClient(...)：那会触发 lifespan，去加载 embedding 模型。
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def student(db):
    return factories.create_user(db, username="student_test", role="student")


@pytest.fixture()
def another_student(db):
    return factories.create_user(db, username="student_other", role="student")


@pytest.fixture()
def admin(db):
    return factories.create_user(db, username="admin_test", role="admin")


@pytest.fixture()
def student_token(client, student):
    return login(client, student.username, DEFAULT_PASSWORD)


@pytest.fixture()
def admin_token(client, admin):
    return login(client, admin.username, DEFAULT_PASSWORD)


@pytest.fixture()
def lab(db):
    return factories.create_lab(db, name="自动化测试实验室")


@pytest.fixture()
def equipment(db, lab):
    return factories.create_equipment(db, lab_id=lab.id, name="测试设备")
