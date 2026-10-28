"""实验室管理接口用例。"""

from __future__ import annotations

import pytest

from tests import factories
from tests.helpers import assert_business_error, assert_success, auth


def test_admin_lab_crud(client, admin_token):
    created = assert_success(
        client.post(
            "/api/lab",
            json={"name": "CRUD实验室", "capacity": 10, "open_time": "08:00", "close_time": "18:00"},
            headers=auth(admin_token),
        )
    )
    lab_id = created["id"]

    detail = assert_success(client.get(f"/api/lab/{lab_id}", headers=auth(admin_token)))
    assert detail["name"] == "CRUD实验室"

    updated = assert_success(
        client.put(
            f"/api/lab/{lab_id}", json={"capacity": 20}, headers=auth(admin_token)
        )
    )
    assert updated["capacity"] == 20

    assert_success(client.delete(f"/api/lab/{lab_id}", headers=auth(admin_token)))
    assert_business_error(
        client.get(f"/api/lab/{lab_id}", headers=auth(admin_token)), "实验室不存在"
    )


def test_student_cannot_create_lab(client, student_token):
    assert_business_error(
        client.post("/api/lab", json={"name": "学生建的"}, headers=auth(student_token)),
        "无权限访问",
        code=403,
    )


def test_duplicate_lab_name(client, admin_token, lab):
    assert_business_error(
        client.post("/api/lab", json={"name": lab.name}, headers=auth(admin_token)),
        "实验室名称已存在",
    )


def test_lab_list_pagination_and_keyword(client, admin_token, db):
    for i in range(3):
        factories.create_lab(db, name=f"分页实验室{i}")

    data = assert_success(
        client.get(
            "/api/lab/list",
            params={"page": 1, "page_size": 2, "keywords": "分页实验室"},
            headers=auth(admin_token),
        )
    )
    assert data["total"] == 3
    assert len(data["list"]) == 2


def test_lab_list_requires_auth(client):
    assert client.get("/api/lab/list").status_code == 401


@pytest.mark.xfail(
    reason="已知缺陷：get_lab_page_list 使用 if status，status=0 被当成未传，无法筛选关闭的实验室",
    strict=False,
)
def test_filter_closed_lab_status_zero(client, admin_token, db):
    factories.create_lab(db, name="开放实验室", status=1)
    factories.create_lab(db, name="关闭实验室", status=0)

    data = assert_success(
        client.get(
            "/api/lab/list",
            params={"status": 0},
            headers=auth(admin_token),
        )
    )
    assert data["total"] == 1
    assert data["list"][0]["status"] == 0


@pytest.mark.xfail(
    reason="已知缺陷：删除仍有设备的实验室触发外键 RESTRICT，返回 500 而不是业务错误",
    strict=False,
)
def test_delete_lab_with_equipment_should_fail_gracefully(client, admin_token, lab, equipment):
    resp = client.delete(f"/api/lab/{lab.id}", headers=auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["code"] != 200
