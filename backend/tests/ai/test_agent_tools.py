"""直接测试 Agent 工具：不经过大模型，断言数据库效果和 JSON 返回。"""

from __future__ import annotations

import json

import pytest

from app.models.reservation import Reservation
from app.services import agent_tools
from tests import factories


def _tools(db, user):
    return {tool.name: tool for tool in agent_tools.build_tools(db, user)}


def test_list_open_labs_only_returns_open_labs(db, student):
    open_lab = factories.create_lab(db, name="开放实验室", status=1)
    factories.create_lab(db, name="关闭实验室", status=0)

    tools = _tools(db, student)
    result = json.loads(tools["list_open_labs"].invoke({"keywords": ""}))

    assert result["total"] == 1
    assert result["labs"][0]["id"] == open_lab.id
    assert result["labs"][0]["name"] == "开放实验室"


def test_list_lab_equipments(db, student, lab, equipment):
    tools = _tools(db, student)
    result = json.loads(
        tools["list_lab_equipments"].invoke({"lab_id": lab.id, "keywords": ""})
    )

    assert result["total"] == 1
    assert result["equipments"][0]["id"] == equipment.id
    assert result["equipments"][0]["lab_id"] == lab.id


def test_get_today_format(db, student):
    tools = _tools(db, student)
    value = tools["get_today"].invoke({})
    assert len(value) == 10
    assert value[4] == "-" and value[7] == "-"


def test_search_lab_docs_delegates_to_kb(db, student, monkeypatch):
    monkeypatch.setattr(
        agent_tools.kb_service, "search", lambda query: f"[预约规则.md]\n{query}"
    )
    tools = _tools(db, student)
    result = tools["search_lab_docs"].invoke({"query": "怎么预约"})
    assert "预约规则.md" in result
    assert "怎么预约" in result


def test_search_lab_docs_empty_result(db, student, monkeypatch):
    monkeypatch.setattr(agent_tools.kb_service, "search", lambda query: "")
    tools = _tools(db, student)
    assert tools["search_lab_docs"].invoke({"query": "无关问题"}) == "没有检索到相关的资料"


def test_create_lab_reservation_tool_writes_row(db, student, lab):
    tools = _tools(db, student)
    payload = {
        "lab_id": lab.id,
        "date": factories.tomorrow(),
        "start_time": "09:00",
        "end_time": "10:00",
        "remark": "工具创建",
    }

    result = json.loads(tools["create_lab_reservation"].invoke(payload))

    assert result["ok"] is True
    row = db.query(Reservation).one()
    assert row.user_id == student.id
    assert row.lab_id == lab.id
    assert row.status == 0
    assert row.remark == "工具创建"


def test_create_lab_reservation_tool_reports_conflict(db, student, lab):
    tools = _tools(db, student)
    payload = {
        "lab_id": lab.id,
        "date": factories.tomorrow(),
        "start_time": "09:00",
        "end_time": "10:00",
    }

    first = json.loads(tools["create_lab_reservation"].invoke(payload))
    second = json.loads(tools["create_lab_reservation"].invoke(payload))

    assert first["ok"] is True
    assert second["ok"] is False
    assert "该时段已预约" in second["error"]


def test_create_lab_reservation_tool_reports_missing_lab(db, student):
    tools = _tools(db, student)
    result = json.loads(
        tools["create_lab_reservation"].invoke(
            {
                "lab_id": 999999,
                "date": factories.tomorrow(),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        )
    )
    assert result["ok"] is False
    assert "实验室不存在" in result["error"]


def test_create_lab_reservation_tool_reports_missing_equipment(db, student, lab):
    tools = _tools(db, student)
    result = json.loads(
        tools["create_lab_reservation"].invoke(
            {
                "lab_id": lab.id,
                "equipment_id": 999999,
                "date": factories.tomorrow(),
                "start_time": "09:00",
                "end_time": "10:00",
            }
        )
    )
    assert result["ok"] is False
    assert "实验室设备不存在" in result["error"]
