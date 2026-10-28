"""用户资料、密码、后台用户管理用例。"""

from __future__ import annotations

import pytest

from tests import factories
from tests.helpers import assert_business_error, assert_success, auth


def test_get_current_user(client, student, student_token):
    data = assert_success(client.get("/api/user/me", headers=auth(student_token)))
    assert data["id"] == student.id
    assert data["username"] == student.username
    assert "password" not in data


def test_update_profile(client, student_token):
    data = assert_success(
        client.put(
            "/api/user/me",
            json={"name": "新名字", "email": "new@example.com", "phone": "13800000000"},
            headers=auth(student_token),
        )
    )
    assert data["name"] == "新名字"
    assert data["email"] == "new@example.com"
    assert data["phone"] == "13800000000"


def test_cannot_escalate_role_via_me(client, student_token):
    data = assert_success(
        client.put(
            "/api/user/me",
            json={"name": "想提权的人", "role": "admin"},
            headers=auth(student_token),
        )
    )
    assert data["role"] == "student"

    assert_business_error(
        client.get("/api/user/list", headers=auth(student_token)),
        "无权限访问",
        code=403,
    )


def test_change_password(client, student, student_token):
    assert_business_error(
        client.put(
            "/api/user/password",
            json={"old_password": "wrong", "new_password": "NewPass@123"},
            headers=auth(student_token),
        ),
        "原密码错误",
    )

    assert_business_error(
        client.put(
            "/api/user/password",
            json={
                "old_password": factories.DEFAULT_PASSWORD,
                "new_password": factories.DEFAULT_PASSWORD,
            },
            headers=auth(student_token),
        ),
        "新旧密码不能相同",
    )

    assert_success(
        client.put(
            "/api/user/password",
            json={
                "old_password": factories.DEFAULT_PASSWORD,
                "new_password": "NewPass@123",
            },
            headers=auth(student_token),
        )
    )

    assert_business_error(
        client.post(
            "/api/auth/login",
            json={"username": student.username, "password": factories.DEFAULT_PASSWORD},
        ),
        "账号或密码错误",
    )
    assert_success(
        client.post(
            "/api/auth/login",
            json={"username": student.username, "password": "NewPass@123"},
        )
    )


def test_admin_list_users(client, admin_token, db):
    factories.create_user(db, username="search_alpha", name="阿尔法")
    factories.create_user(db, username="search_beta", name="贝塔")

    data = assert_success(
        client.get(
            "/api/user/list",
            params={"keywords": "search_"},
            headers=auth(admin_token),
        )
    )
    assert data["total"] >= 2


def test_student_cannot_list_users(client, student_token):
    assert_business_error(
        client.get("/api/user/list", headers=auth(student_token)),
        "无权限访问",
        code=403,
    )


def test_admin_cannot_delete_self(client, admin, admin_token):
    assert_business_error(
        client.delete(f"/api/user/{admin.id}", headers=auth(admin_token)),
        "不能删除当前登录的账号",
    )


@pytest.mark.xfail(
    reason="已知缺陷：UserUpdateRequest 被重复定义，第二个定义丢失 role/status，管理员改角色被静默忽略",
    strict=False,
)
def test_admin_can_update_user_role(client, admin_token, student):
    data = assert_success(
        client.put(
            f"/api/user/{student.id}",
            json={"role": "admin"},
            headers=auth(admin_token),
        )
    )
    assert data["role"] == "admin"


@pytest.mark.xfail(
    reason="已知缺陷：删除仍有预约的用户触发外键 RESTRICT，返回 500 而不是业务错误",
    strict=False,
)
def test_delete_user_with_reservations_should_fail_gracefully(
    client, admin_token, db, another_student, lab
):
    factories.create_reservation(
        db, user_id=another_student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    resp = client.delete(f"/api/user/{another_student.id}", headers=auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["code"] != 200
