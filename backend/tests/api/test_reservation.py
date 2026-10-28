"""预约核心业务用例：冲突、状态机、权限、过期与并发。"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.common.exceptions import BusinessException
from app.database import SessionLocal
from app.schemas.reservation import ReservationCreateRequest
from app.services import reservation_service
from tests import factories
from tests.helpers import (
    assert_business_error,
    assert_success,
    auth,
    create_reservation_payload,
)


def _reserve(client, token, **kwargs):
    return client.post(
        "/api/reservation", json=create_reservation_payload(**kwargs), headers=auth(token)
    )


def test_create_reservation_success(client, student_token, lab):
    assert_success(_reserve(client, student_token, lab_id=lab.id, date=factories.tomorrow()))

    data = assert_success(
        client.get("/api/reservation/list", headers=auth(student_token))
    )
    assert data["total"] == 1
    item = data["list"][0]
    assert item["status"] == 0
    assert item["type"] == "实验室"
    assert item["lab_name"] == lab.name


def test_create_reservation_past_date(client, student_token, lab):
    assert_business_error(
        _reserve(client, student_token, lab_id=lab.id, date=factories.yesterday()),
        "预约日期不能小于当前的日期",
    )


def test_end_time_before_start_time(client, student_token, lab):
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            date=factories.tomorrow(),
            start_time="11:00",
            end_time="10:00",
        ),
        "预约的结束时间不能小于开始时间",
    )


def test_nonexistent_lab(client, student_token):
    assert_business_error(
        _reserve(client, student_token, lab_id=999999, date=factories.tomorrow()),
        "实验室不存在",
    )


def test_closed_lab(client, student_token, db):
    closed = factories.create_lab(db, name="关闭的实验室", status=0)
    assert_business_error(
        _reserve(client, student_token, lab_id=closed.id, date=factories.tomorrow()),
        "实验室已关闭",
    )


def test_outside_open_time(client, student_token, lab):
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            date=factories.tomorrow(),
            start_time="07:00",
            end_time="09:00",
        ),
        "不能早于实验室的开放时间",
    )
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            date=factories.tomorrow(),
            start_time="17:00",
            end_time="19:00",
        ),
        "不能晚于实验室的关闭时间",
    )


def test_equipment_not_found(client, student_token, lab):
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            equipment_id=999999,
            date=factories.tomorrow(),
        ),
        "实验室设备不存在",
    )


def test_equipment_under_repair(client, student_token, db, lab):
    broken = factories.create_equipment(db, lab_id=lab.id, name="维修设备", status=0)
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            equipment_id=broken.id,
            date=factories.tomorrow(),
        ),
        "实验室设备正在维修",
    )


def test_overlap_same_lab_rejected(client, student_token, lab):
    payload = dict(lab_id=lab.id, date=factories.tomorrow())
    assert_success(_reserve(client, student_token, **payload, start_time="09:00", end_time="10:00"))
    assert_business_error(
        _reserve(client, student_token, **payload, start_time="09:30", end_time="10:30"),
        "该时段已预约",
    )


def test_adjacent_time_allowed(client, student_token, lab):
    payload = dict(lab_id=lab.id, date=factories.tomorrow())
    assert_success(_reserve(client, student_token, **payload, start_time="09:00", end_time="10:00"))
    assert_success(_reserve(client, student_token, **payload, start_time="10:00", end_time="11:00"))


def test_list_scope_student_and_admin(client, student_token, admin_token, db, student, another_student, lab):
    factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    factories.create_reservation(
        db, user_id=another_student.id, lab_id=lab.id, date=factories.tomorrow(),
        start_time="11:00", end_time="12:00",
    )

    own = assert_success(client.get("/api/reservation/list", headers=auth(student_token)))
    assert own["total"] == 1
    assert own["list"][0]["user_id"] == student.id

    all_items = assert_success(client.get("/api/reservation/list", headers=auth(admin_token)))
    assert all_items["total"] == 2


def test_cancel_own_pending(client, student_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    assert_success(
        client.put(f"/api/reservation/{item.id}/cancel", headers=auth(student_token))
    )
    # 结束当前事务，否则 REPEATABLE READ 快照看不到接口请求的提交
    db.rollback()
    assert db.get(type(item), item.id).status == 3


def test_cancel_other_student_forbidden(client, student_token, db, another_student, lab):
    item = factories.create_reservation(
        db, user_id=another_student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    assert_business_error(
        client.put(f"/api/reservation/{item.id}/cancel", headers=auth(student_token)),
        "无权限",
        code=403,
    )


def test_cancel_rejected_reservation(client, student_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow(), status=2
    )
    assert_business_error(
        client.put(f"/api/reservation/{item.id}/cancel", headers=auth(student_token)),
        "当前状态无法取消",
    )


def test_admin_audit_approve(client, admin_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    assert_success(
        client.put(
            f"/api/reservation/{item.id}/audit",
            json={"status": 1},
            headers=auth(admin_token),
        )
    )
    db.rollback()
    assert db.get(type(item), item.id).status == 1


def test_audit_invalid_status(client, admin_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    assert_business_error(
        client.put(
            f"/api/reservation/{item.id}/audit",
            json={"status": 3},
            headers=auth(admin_token),
        ),
        "审核状态错误",
    )


def test_audit_twice_rejected(client, admin_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow(), status=1
    )
    assert_business_error(
        client.put(
            f"/api/reservation/{item.id}/audit",
            json={"status": 1},
            headers=auth(admin_token),
        ),
        "当前状态不支持审核",
    )


def test_student_cannot_audit(client, student_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow()
    )
    assert_business_error(
        client.put(
            f"/api/reservation/{item.id}/audit",
            json={"status": 1},
            headers=auth(student_token),
        ),
        "无权限访问",
        code=403,
    )


def test_audit_nonexistent_reservation(client, admin_token):
    assert_business_error(
        client.put(
            "/api/reservation/999999/audit",
            json={"status": 1},
            headers=auth(admin_token),
        ),
        "预约记录不存在",
    )

def test_create_reservation_require_login(client, lab):
    resp = client.post(
        "/api/reservation",
        json = create_reservation_payload(lab_id=lab.id, date=factories.tomorrow()),
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 已知缺陷：以下用例断言的是“正确行为”，当前实现会失败，用 xfail 标记。
# strict=False：修好后会变成 XPASS，不会阻塞 CI。
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="已知缺陷：end_time == start_time 的零时长预约被放行", strict=False)
def test_zero_length_reservation_should_be_rejected(client, student_token, lab):
    resp = _reserve(
        client,
        student_token,
        lab_id=lab.id,
        date=factories.tomorrow(),
        start_time="10:00",
        end_time="10:00",
    )
    assert resp.json()["code"] != 200


@pytest.mark.xfail(reason="已知缺陷：日期没有格式校验，'not-a-date' 会被当成未来日期落库", strict=False)
def test_malformed_date_should_be_rejected(client, student_token, lab):
    resp = _reserve(client, student_token, lab_id=lab.id, date="not-a-date")
    assert resp.json()["code"] != 200


@pytest.mark.xfail(
    reason="已知缺陷：时间按字符串比较，合法的 '9:00'-'10:00' 被误判为结束时间小于开始时间",
    strict=False,
)
def test_time_without_leading_zero_should_be_accepted(client, student_token, lab):
    resp = _reserve(
        client,
        student_token,
        lab_id=lab.id,
        date=factories.tomorrow(),
        start_time="9:00",
        end_time="10:00",
    )
    assert resp.json()["code"] == 200


@pytest.mark.xfail(
    reason="已知缺陷：预约设备时不校验设备是否属于传入的实验室，可跨实验室预约", strict=False
)
def test_equipment_must_belong_to_the_lab(client, student_token, db, lab):
    other_lab = factories.create_lab(db, name="另一个实验室")
    other_equipment = factories.create_equipment(db, lab_id=other_lab.id, name="别家设备")

    resp = _reserve(
        client,
        student_token,
        lab_id=lab.id,
        equipment_id=other_equipment.id,
        date=factories.tomorrow(),
    )
    assert resp.json()["code"] != 200


@pytest.mark.xfail(
    reason="已知缺陷（知识库规则）：约了设备，时段内实验室也应占用，当前分开查重", strict=False
)
def test_equipment_booking_should_block_lab_booking(client, student_token, db, lab, equipment):
    date = factories.tomorrow()
    assert_success(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            equipment_id=equipment.id,
            date=date,
            start_time="09:00",
            end_time="10:00",
        )
    )
    resp = _reserve(
        client,
        student_token,
        lab_id=lab.id,
        date=date,
        start_time="09:30",
        end_time="10:30",
    )
    assert resp.json()["code"] != 200


@pytest.mark.xfail(
    reason="已知缺陷（知识库规则）：实验室被预约后，同时段设备预约也应冲突", strict=False
)
def test_lab_booking_should_block_equipment_booking(client, student_token, db, lab, equipment):
    date = factories.tomorrow()
    assert_success(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            date=date,
            start_time="09:00",
            end_time="10:00",
        )
    )
    resp = _reserve(
        client,
        student_token,
        lab_id=lab.id,
        equipment_id=equipment.id,
        date=date,
        start_time="09:30",
        end_time="10:30",
    )
    assert resp.json()["code"] != 200


@pytest.mark.xfail(
    reason="已知缺陷（知识库规则）：已通过的预约本人也应能取消，当前只允许待审核取消",
    strict=False,
)
def test_cancel_approved_reservation_should_be_allowed(client, student_token, db, student, lab):
    item = factories.create_reservation(
        db, user_id=student.id, lab_id=lab.id, date=factories.tomorrow(), status=1
    )
    resp = client.put(
        f"/api/reservation/{item.id}/cancel", headers=auth(student_token)
    )
    assert resp.json()["code"] == 200


@pytest.mark.xfail(
    reason="已知缺陷：过期扫描在没有过期单时 changed 未初始化，抛 UnboundLocalError",
    strict=False,
)
def test_expire_scan_should_not_crash_when_nothing_to_expire(db, lab):
    # 没有待审核预约时调用，正确实现应当安静返回
    reservation_service.expire_pending_reservation()


def test_expire_pending_reservation(db, student, lab):
    expired = factories.create_reservation(
        db,
        user_id=student.id,
        lab_id=lab.id,
        date=factories.yesterday(),
        status=0,
    )
    approved = factories.create_reservation(
        db,
        user_id=student.id,
        lab_id=lab.id,
        date=factories.yesterday(),
        start_time="11:00",
        end_time="12:00",
        status=1,
    )

    reservation_service.expire_pending_reservation()

    db.rollback()
    assert db.get(type(expired), expired.id).status == 3
    assert db.get(type(approved), approved.id).status == 1


@pytest.mark.xfail(
    reason="已知缺陷：先查冲突再插入，无唯一约束/锁，并发下同一时段可能重复预约",
    strict=False,
)
def test_concurrent_same_slot_only_one_succeeds(db, student, lab):
    date = factories.tomorrow()
    request = ReservationCreateRequest(
        lab_id=lab.id, date=date, start_time="09:00", end_time="10:00"
    )
    user_stub = SimpleNamespace(id=student.id)
    workers = 8
    barrier = threading.Barrier(workers)

    def worker() -> bool:
        session = SessionLocal()
        try:
            barrier.wait(timeout=10)
            reservation_service.create_reservation(session, user_stub, request)
            return True
        except BusinessException:
            return False
        except Exception:
            return False
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: worker(), range(workers)))

    assert sum(results) == 1


def test_create_reservation_today_with_past_start_time(client, student_token, lab):
    now = datetime.now()
    if now.hour == 0:
        pytest.skip("凌晨 0 点附近无法构造当天已过去的时间")

    start = (now - timedelta(hours=1)).strftime("%H:%M")
    end = (now - timedelta(minutes=1)).strftime("%H:%M")
    assert_business_error(
        _reserve(
            client,
            student_token,
            lab_id=lab.id,
            date=now.strftime("%Y-%m-%d"),
            start_time=start,
            end_time=end,
        ),
        "预约开始时间不能小于当前的时间",
    )

