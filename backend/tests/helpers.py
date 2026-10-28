"""接口测试通用断言与请求辅助。"""

from __future__ import annotations

DEFAULT_PASSWORD = "Test@123456"


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client, username: str, password: str = DEFAULT_PASSWORD) -> str:
    resp = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 200, body
    return body["data"]["token"]


def assert_success(resp) -> object:
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == 200, body
    return body.get("data")


def assert_business_error(resp, message: str | None = None, code: int = 500) -> dict:
    """业务异常统一是 HTTP 200 + body.code != 200，不能只看 HTTP 状态码。"""
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == code, body
    if message is not None:
        assert message in body["message"], body
    return body


def assert_http_error(resp, status_code: int) -> dict:
    assert resp.status_code == status_code, resp.text
    body = resp.json()
    assert body["code"] == status_code, body
    return body


def create_reservation_payload(
    *,
    lab_id: int,
    date: str,
    start_time: str = "09:00",
    end_time: str = "10:00",
    equipment_id: int | None = None,
    remark: str | None = None,
) -> dict:
    return {
        "lab_id": lab_id,
        "equipment_id": equipment_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "remark": remark,
    }
