"""鉴权与账号相关用例。"""

from __future__ import annotations

import time

import jwt
import pytest

from app.config import settings
from tests import factories
from tests.helpers import assert_business_error, assert_http_error, assert_success, auth


def test_register_and_login(client):
    assert_success(
        client.post(
            "/api/auth/register",
            json={"username": "new_student", "password": "Pass@123", "name": "新同学"},
        )
    )

    body = assert_success(
        client.post(
            "/api/auth/login",
            json={"username": "new_student", "password": "Pass@123"},
        )
    )
    assert body["token"]
    assert body["user"]["username"] == "new_student"
    assert body["user"]["role"] == "student"


# def test_register_duplicate_username(client):
#     payload = {"username": "dup_user", "password": "Pass@123"}
#     assert_success(client.post("/api/auth/register", json=payload))
#     assert_business_error(
#         client.post("/api/auth/register", json=payload), "账号已存在"
#     )

def test_register_duplicate_username(client):
    # arrange 准备，定义payload，需要哪些数据，谁登录
    payload = {"username": "dup_user", "password": "Pass@123"}
    # act 执行，调注册接口，用户做了什么操作
    assert_success(client.post("/api/auth/register", json=payload))
    # assert 断言，检查返回“账号已存在”预期结果是什么
    assert_business_error(client.post("/api/auth/register", json=payload), "账号已存在")




def test_login_wrong_password(client, student):
    assert_business_error(
        client.post(
            "/api/auth/login",
            json={"username": student.username, "password": "wrong-password"},
        ),
        "账号或密码错误",
    )


def test_login_disabled_user(client, db):
    user = factories.create_user(db, username="disabled_user", status=0)
    assert_business_error(
        client.post(
            "/api/auth/login",
            json={"username": user.username, "password": factories.DEFAULT_PASSWORD},
        ),
        "账号被禁用",
    )


def test_missing_token_returns_401(client):
    assert_http_error(client.get("/api/user/me"), 401)


def test_invalid_token_returns_401(client):
    assert_http_error(client.get("/api/user/me", headers=auth("not-a-jwt")), 401)


def test_expired_token_returns_401(client, student):
    # 用 epoch 秒，避免本地时间与 UTC 的时区差把“已过期”算成未过期
    token = jwt.encode(
        {"user_id": student.id, "exp": int(time.time()) - 60},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    assert_http_error(client.get("/api/user/me", headers=auth(token)), 401)


def test_student_cannot_access_admin_api(client, student_token):
    body = assert_business_error(
        client.get("/api/user/list", headers=auth(student_token)), "无权限访问", code=403
    )
    assert body["code"] == 403


@pytest.mark.xfail(
    reason="已知缺陷：token 对应用户被删除后，get_current_user 未判空，返回 500 而不是 401",
    strict=False,
)
def test_token_of_deleted_user_should_return_401(client, db, student, student_token):
    db.delete(student)
    db.commit()

    resp = client.get("/api/user/me", headers=auth(student_token))
    assert_http_error(resp, 401)


@pytest.mark.xfail(
    reason="已知缺陷：注册接口允许空用户名/空密码，应按参数校验拒绝",
    strict=False,
)
def test_register_empty_credentials_should_be_rejected(client):
    resp = client.post("/api/auth/register", json={"username": "", "password": ""})
    assert resp.status_code == 422 or resp.json()["code"] != 200
