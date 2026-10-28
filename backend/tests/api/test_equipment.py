"""设备管理接口用例。"""

from __future__ import annotations

import pytest

from tests import factories
from tests.helpers import assert_business_error, assert_success, auth


def test_admin_equipment_crud(client, admin_token, lab):
    created = assert_success(
        client.post(
            "/api/equipment",
            json={"lab_id": lab.id, "name": "CRUD设备", "quantity": 2},
            headers=auth(admin_token),
        )
    )
    equipment_id = created["id"]
    assert created["lab_name"] == lab.name

    updated = assert_success(
        client.put(
            f"/api/equipment/{equipment_id}",
            json={"quantity": 5},
            headers=auth(admin_token),
        )
    )
    assert updated["quantity"] == 5

    assert_success(
        client.delete(f"/api/equipment/{equipment_id}", headers=auth(admin_token))
    )


def test_equipment_list_filter_by_lab(client, admin_token, db, lab):
    other_lab = factories.create_lab(db, name="另一个实验室")
    factories.create_equipment(db, lab_id=lab.id, name="本实验室设备")
    factories.create_equipment(db, lab_id=other_lab.id, name="别家设备")

    data = assert_success(
        client.get(
            "/api/equipment/list",
            params={"lab_id": lab.id},
            headers=auth(admin_token),
        )
    )
    assert data["total"] == 1
    assert data["list"][0]["lab_id"] == lab.id


def test_duplicate_equipment_name_in_same_lab(client, admin_token, lab):
    payload = {"lab_id": lab.id, "name": "同名设备"}
    assert_success(client.post("/api/equipment", json=payload, headers=auth(admin_token)))
    assert_business_error(
        client.post("/api/equipment", json=payload, headers=auth(admin_token)),
        "实验室设备已存在",
    )


def test_student_cannot_create_equipment(client, student_token, lab):
    assert_business_error(
        client.post(
            "/api/equipment",
            json={"lab_id": lab.id, "name": "学生设备"},
            headers=auth(student_token),
        ),
        "无权限访问",
        code=403,
    )


@pytest.mark.xfail(
    reason="已知缺陷：创建设备时不校验 lab_id 是否存在，外键错误直接 500",
    strict=False,
)
def test_create_equipment_with_missing_lab_should_fail_gracefully(client, admin_token):
    resp = client.post(
        "/api/equipment",
        json={"lab_id": 999999, "name": "不存在实验室的设备"},
        headers=auth(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["code"] != 200


@pytest.mark.xfail(
    reason="已知缺陷：删除仍被预约引用的设备触发外键 RESTRICT，返回 500",
    strict=False,
)
def test_delete_equipment_with_reservation_should_fail_gracefully(
    client, admin_token, db, student, lab, equipment
):
    factories.create_reservation(
        db,
        user_id=student.id,
        lab_id=lab.id,
        equipment_id=equipment.id,
        date=factories.tomorrow(),
    )
    resp = client.delete(f"/api/equipment/{equipment.id}", headers=auth(admin_token))
    assert resp.status_code == 200
    assert resp.json()["code"] != 200
