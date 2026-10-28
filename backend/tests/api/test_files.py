"""文件上传接口用例。"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config import UPLOAD_DIR
from tests.helpers import assert_business_error, assert_success


def _cleanup(url: str) -> None:
    name = url.rsplit("/", 1)[-1]
    Path(UPLOAD_DIR, name).unlink(missing_ok=True)


def test_upload_allowed_extension(client):
    resp = client.post(
        "/api/files/upload",
        files={"file": ("avatar.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    data = assert_success(resp)
    try:
        assert data["original_name"] == "avatar.jpg"
        assert data["url"].startswith("/uploads/")
        assert data["size"] == len(b"fake-image-bytes")

        served = client.get(data["url"])
        assert served.status_code == 200
        assert served.content == b"fake-image-bytes"
    finally:
        _cleanup(data["url"])


def test_upload_extension_is_case_insensitive(client):
    resp = client.post(
        "/api/files/upload",
        files={"file": ("photo.JPG", b"bytes", "image/jpeg")},
    )
    data = assert_success(resp)
    try:
        assert data["original_name"] == "photo.JPG"
    finally:
        _cleanup(data["url"])


def test_upload_disallowed_extension(client):
    assert_business_error(
        client.post(
            "/api/files/upload",
            files={"file": ("shell.exe", b"MZ", "application/octet-stream")},
        ),
        "不支持的文件后缀",
    )


def test_upload_size_limit(client, monkeypatch):
    import app.api.files as files_api

    monkeypatch.setattr(files_api, "MAX_FILE_SIZE", 1024)
    assert_business_error(
        client.post(
            "/api/files/upload",
            files={"file": ("big.jpg", b"x" * 2048, "image/jpeg")},
        ),
        "文件不能超过",
    )


def test_upload_filename_path_is_stripped(client):
    resp = client.post(
        "/api/files/upload",
        files={"file": ("../../evil.jpg", b"bytes", "image/jpeg")},
    )
    data = assert_success(resp)
    try:
        assert data["original_name"] == "evil.jpg"
        assert ".." not in data["disk_name"]
    finally:
        _cleanup(data["url"])


@pytest.mark.xfail(
    reason="已知缺陷：上传接口未做鉴权，匿名用户也能上传文件", strict=False
)
def test_upload_requires_authentication(client):
    resp = client.post(
        "/api/files/upload",
        files={"file": ("anonymous.jpg", b"bytes", "image/jpeg")},
    )
    try:
        assert resp.status_code == 401
    finally:
        if resp.status_code == 200 and resp.json().get("data"):
            _cleanup(resp.json()["data"]["url"])
