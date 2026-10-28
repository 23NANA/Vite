"""服务层边界用例：冲突判定与状态对占用的影响。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.exceptions import BusinessException
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreateRequest
from app.services import reservation_service
from tests import factories


def _create(db, student, lab, *, start: str, end: str, status: int = 0, equipment_id=None):
    return factories.create_reservation(
        db,
        user_id=student.id,
        lab_id=lab.id,
        date=factories.tomorrow(),
        start_time=start,
        end_time=end,
        status=status,
        equipment_id=equipment_id,
    )


def _book(db, student, lab, *, start: str, end: str, equipment_id=None):
    data = ReservationCreateRequest(
        lab_id=lab.id,
        equipment_id=equipment_id,
        date=factories.tomorrow(),
        start_time=start,
        end_time=end,
    )
    reservation_service.create_reservation(db, SimpleNamespace(id=student.id), data)


def test_touching_boundaries_do_not_conflict(db, student, lab):
    _book(db, student, lab, start="09:00", end="10:00")
    _book(db, student, lab, start="10:00", end="11:00")

    assert db.query(Reservation).count() == 2


def test_overlap_conflicts(db, student, lab):
    _book(db, student, lab, start="09:00", end="10:00")
    with pytest.raises(BusinessException, match="该时段已预约"):
        _book(db, student, lab, start="09:59", end="10:01")


def test_cancelled_reservation_does_not_block(db, student, lab):
    _create(db, student, lab, start="09:00", end="10:00", status=3)
    _book(db, student, lab, start="09:00", end="10:00")


def test_rejected_reservation_does_not_block(db, student, lab):
    _create(db, student, lab, start="09:00", end="10:00", status=2)
    _book(db, student, lab, start="09:00", end="10:00")


def test_pending_reservation_blocks(db, student, lab):
    _create(db, student, lab, start="09:00", end="10:00", status=0)
    with pytest.raises(BusinessException, match="该时段已预约"):
        _book(db, student, lab, start="09:30", end="10:30")


def test_approved_reservation_blocks(db, student, lab):
    _create(db, student, lab, start="09:00", end="10:00", status=1)
    with pytest.raises(BusinessException, match="该时段已预约"):
        _book(db, student, lab, start="09:30", end="10:30")


def test_audit_invalid_status_raises(db, student, lab):
    item = _create(db, student, lab, start="09:00", end="10:00")
    with pytest.raises(BusinessException, match="审核状态错误"):
        reservation_service.audit_reservation(db, item.id, 0)


def test_audit_nonexistent_raises(db):
    with pytest.raises(BusinessException, match="预约记录不存在"):
        reservation_service.audit_reservation(db, 999999, 1)
