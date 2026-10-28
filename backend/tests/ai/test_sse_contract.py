"""SSE 流式接口契约测试：用假 Agent 固定事件序列，不调用真实大模型。"""

from __future__ import annotations

import json
from types import SimpleNamespace

from app.services import agent_service
from tests.helpers import auth


class FakeAgent:
    def __init__(self, events, error: Exception | None = None):
        self.events = events
        self.error = error

    async def astream_events(self, inputs, version="v2", config=None):
        for event in self.events:
            yield event
        if self.error is not None:
            raise self.error


def _stream_events(client, payload, token=None, headers=None):
    request_headers = headers if headers is not None else (auth(token) if token else {})
    with client.stream(
        "POST", "/api/ai/chat/stream", json=payload, headers=request_headers
    ) as resp:
        assert resp.status_code == 200, resp.text
        assert "text/event-stream" in resp.headers["content-type"]
        events = []
        for line in resp.iter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
        return events


def test_sse_event_sequence(client, student_token, monkeypatch):
    fake_events = [
        {"event": "on_tool_start", "name": "list_open_labs", "data": {}},
        {
            "event": "on_tool_end",
            "name": "list_open_labs",
            "data": {"output": '{"total": 0, "labs": []}'},
        },
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "agent"},
            "data": {"chunk": SimpleNamespace(content="你好")},
        },
    ]
    monkeypatch.setattr(
        agent_service, "build_agent", lambda db, user: FakeAgent(fake_events)
    )

    events = _stream_events(
        client, {"messages": [{"role": "user", "content": "有哪些实验室"}]}, student_token
    )

    assert [event["type"] for event in events] == [
        "status",
        "tool_start",
        "tool_end",
        "token",
        "done",
    ]
    assert events[1]["name"] == "list_open_labs"
    assert events[1]["label"] == "查询开放实验室"
    assert events[2]["preview"].startswith('{"total": 0')
    assert events[3]["content"] == "你好"


def test_sse_agent_error_becomes_error_event(client, student_token, monkeypatch):
    monkeypatch.setattr(
        agent_service, "build_agent", lambda db, user: FakeAgent([], RuntimeError("boom"))
    )
    monkeypatch.setattr(agent_service.traceback, "print_exc", lambda *args, **kwargs: None)

    events = _stream_events(
        client, {"messages": [{"role": "user", "content": "你好"}]}, student_token
    )

    assert events[0]["type"] == "status"
    assert events[-1] == {"type": "error", "message": "大模型调用失败，请稍后重试"}


def test_sse_empty_messages_returns_error_event(client, student_token):
    events = _stream_events(client, {"messages": []}, student_token)

    assert events == [{"type": "error", "message": "请输入您的对话内容"}]


def test_sse_requires_authentication(client):
    resp = client.post(
        "/api/ai/chat/stream", json={"messages": [{"role": "user", "content": "hi"}]}
    )
    assert resp.status_code == 401


def test_non_stream_chat_returns_assistant_message(client, student_token, monkeypatch):
    monkeypatch.setattr(agent_service, "run_agent", lambda db, user, data: "回答内容")

    resp = client.post(
        "/api/ai/chat",
        json={"messages": [{"role": "user", "content": "你好"}]},
        headers=auth(student_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    assert body["data"] == {"role": "assistant", "content": "回答内容"}
