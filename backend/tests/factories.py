"""测试数据工厂：直接落库，避免每个用例都通过接口准备数据。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.utils.password import hash_password

DEFAULT_PASSWORD = "Test@123456"


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_user(
    db: Session,
    *,
    username: str | None = None,
    password: str = DEFAULT_PASSWORD,
    name: str | None = None,
    role: str = "student",
    status: int = 1,
    email: str | None = None,
    phone: str | None = None,
) -> User:
    user = User(
        username=username or _unique("user"),
        password=hash_password(password),
        name=name or "测试用户",
        role=role,
        status=status,
        email=email,
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_lab(
    db: Session,
    *,
    name: str | None = None,
    location: str = "综合实验楼101",
    capacity: int = 30,
    open_time: str | None = "08:00",
    close_time: str | None = "18:00",
    status: int = 1,
    description: str | None = "自动化测试用实验室",
) -> Lab:
    lab = Lab(
        name=name or _unique("实验室"),
        location=location,
        capacity=capacity,
        open_time=open_time,
        close_time=close_time,
        description=description,
        status=status,
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab


def create_equipment(
    db: Session,
    *,
    lab_id: int,
    name: str | None = None,
    quantity: int = 1,
    status: int = 1,
    spec: str | None = "TEST-SPEC",
) -> Equipment:
    equipment = Equipment(
        lab_id=lab_id,
        name=name or _unique("设备"),
        quantity=quantity,
        status=status,
        spec=spec,
        description="自动化测试用设备",
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def create_reservation(
    db: Session,
    *,
    user_id: int,
    lab_id: int,
    date: str | None = None,
    start_time: str = "09:00",
    end_time: str = "10:00",
    equipment_id: int | None = None,
    remark: str | None = None,
    status: int = 0,
) -> Reservation:
    reservation = Reservation(
        user_id=user_id,
        lab_id=lab_id,
        equipment_id=equipment_id,
        date=date or tomorrow(),
        start_time=start_time,
        end_time=end_time,
        remark=remark,
        status=status,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def tomorrow() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
