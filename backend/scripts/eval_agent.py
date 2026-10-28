#!/usr/bin/env python
"""端到端 Agent 评测。

在独立的 *_eval / *_test 数据库上跑，不碰开发库。

用法（在 backend 目录下）：

    # 1. 只校验数据集和数据库，不调用大模型
    .venv/Scripts/python.exe scripts/eval_agent.py --dry-run

    # 2. 跑真实 Agent（会调用 LLM_API_KEY 对应的模型，产生费用）
    .venv/Scripts/python.exe scripts/eval_agent.py

    # 3. 额外调用 LLM-as-Judge 做四维打分
    .venv/Scripts/python.exe scripts/eval_agent.py --judge

    # 4. 只跑前 3 条
    .venv/Scripts/python.exe scripts/eval_agent.py --limit 3 --judge

评测维度：
- 工具调用：期望工具是否全部调用、是否调用了禁止工具
- 答案要点：回复是否包含预期关键词（避免只靠 Judge）
- 真实落库：预约数量是否与预期一致（防止“嘴上说预约成功”）
- LLM-as-Judge：相关性、准确性、完整性、有用性，各 1-5 分
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _prepare_eval_database() -> str:
    """强制把 DATABASE_URL 切到独立评测库，避免误清开发数据。"""
    from sqlalchemy.engine import make_url

    explicit = os.environ.get("EVAL_DATABASE_URL")
    if explicit:
        eval_url = explicit
    else:
        base = os.environ.get("DATABASE_URL") or _read_env_file(ROOT / ".env").get(
            "DATABASE_URL"
        )
        if not base:
            raise SystemExit(
                "未找到数据库配置：请设置 EVAL_DATABASE_URL，或在 backend/.env 配置 DATABASE_URL。"
            )
        eval_url = make_url(base).set(database="lab_agent_eval").render_as_string(
            hide_password=False
        )

    url = make_url(eval_url)
    if not url.database or not (
        url.database.endswith("_eval") or url.database.endswith("_test")
    ):
        raise SystemExit(
            f"拒绝在数据库 {url.database!r} 上运行评测。"
            "库名必须以 _eval 或 _test 结尾，或显式设置 EVAL_DATABASE_URL。"
        )

    import pymysql

    try:
        conn = pymysql.connect(
            host=url.host or "127.0.0.1",
            port=url.port or 3306,
            user=url.username,
            password=url.password or "",
        )
    except Exception as exc:
        raise SystemExit(
            f"无法连接 MySQL {url.host or '127.0.0.1'}:{url.port or 3306}：{exc}\n"
            "请确认 MySQL 已启动，或在 backend/.env 配置 DATABASE_URL / 设置 EVAL_DATABASE_URL。"
        ) from exc
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    os.environ["DATABASE_URL"] = eval_url
    return eval_url


EVAL_DATABASE_URL = _prepare_eval_database()


def _safe_database_url(url: str) -> str:
    from sqlalchemy.engine import make_url

    return make_url(url).render_as_string(hide_password=True)

from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.equipment import Equipment  # noqa: E402
from app.models.lab import Lab  # noqa: E402
from app.models.reservation import Reservation  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.ai import ChatMessage, ChatRequest  # noqa: E402
from app.services import agent_service  # noqa: E402
from tests import factories  # noqa: E402

DIMENSIONS = ("relevance", "accuracy", "completeness", "helpfulness")

JUDGE_SYSTEM = """你是严格、客观的 Agent 评测员。请根据用户问题、参考要点、工具调用记录和 Agent 回复打分。
四个维度各 1-5 分：
- relevance：是否直接回答用户问题，不跑题。
- accuracy：事实是否与参考要点一致，是否编造了不存在的信息。
- completeness：是否覆盖回答该问题所需的关键信息。
- helpfulness：表达是否清晰，是否给出可执行的下一步。
只输出一个 JSON 对象，不要输出 markdown：
{"relevance": 1-5, "accuracy": 1-5, "completeness": 1-5, "helpfulness": 1-5, "reason": "一句话理由"}"""


def load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise SystemExit(f"{path} 必须是非空 JSON 数组")
    ids = set()
    for case in data:
        if not case.get("id") or not case.get("turns"):
            raise SystemExit(f"{path} 存在缺少 id 或 turns 的用例：{case}")
        if case["id"] in ids:
            raise SystemExit(f"{path} 存在重复 id：{case['id']}")
        ids.add(case["id"])
    return data


def reset_database() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def seed_database() -> int:
    """建一套确定性的评测数据，返回学生 ID。"""
    with SessionLocal() as db:
        student = factories.create_user(
            db, username="eval_student", name="评测学生", role="student"
        )
        cloud = factories.create_lab(
            db,
            name="云计算实验室",
            location="实验楼A301",
            capacity=40,
            open_time="08:00",
            close_time="21:00",
        )
        factories.create_lab(
            db,
            name="化学实验室",
            location="实验楼B102",
            capacity=30,
            open_time="08:30",
            close_time="18:00",
        )
        factories.create_lab(
            db,
            name="物理实验室",
            location="实验楼C201",
            capacity=25,
            open_time="08:00",
            close_time="20:00",
        )
        factories.create_lab(
            db,
            name="计算机实验室",
            location="实验楼A101",
            capacity=50,
            open_time="08:00",
            close_time="21:00",
        )
        factories.create_equipment(
            db, lab_id=cloud.id, name="GPU服务器", spec="8 x A100", quantity=2
        )
        return student.id


def reset_reservations(student_id: int, seed_reservation: bool) -> None:
    with SessionLocal() as db:
        db.query(Reservation).delete()
        db.commit()
        if seed_reservation:
            first_lab = db.query(Lab).order_by(Lab.id).first()
            factories.create_reservation(
                db,
                user_id=student_id,
                lab_id=first_lab.id,
                date=factories.tomorrow(),
                start_time="11:00",
                end_time="12:00",
                status=0,
            )


def count_reservations() -> int:
    with SessionLocal() as db:
        return db.query(Reservation).count()


async def run_case(student_id: int, case: dict) -> dict:
    student = SimpleNamespace(id=student_id)
    messages: list[ChatMessage] = []
    tool_calls: list[str] = []
    errors: list[str] = []
    answer = ""

    for turn in case["turns"]:
        messages.append(ChatMessage(role="user", content=turn))
        answer = ""
        async for event in agent_service.stream_gent(
            student, ChatRequest(messages=messages)
        ):
            kind = event.get("type")
            if kind == "tool_start":
                tool_calls.append(event.get("name") or "")
            elif kind == "token":
                answer += event.get("content") or ""
            elif kind == "error":
                errors.append(event.get("message") or "")
        messages.append(ChatMessage(role="assistant", content=answer))

    return {"answer": answer, "tool_calls": tool_calls, "errors": errors}


def check_tools(case: dict, actual: list[str]) -> bool:
    expected = case.get("expected_tools", [])
    expected_any = case.get("expected_any_tools", [])
    forbidden = case.get("forbidden_tools", [])
    if any(name not in actual for name in expected):
        return False
    if expected_any and not any(name in actual for name in expected_any):
        return False
    if any(name in actual for name in forbidden):
        return False
    return True


def check_answer(case: dict, answer: str) -> bool:
    keywords = case.get("answer_contains_any", [])
    return not keywords or any(keyword in answer for keyword in keywords)


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Judge 没有返回 JSON：{text[:200]}")
    return json.loads(text[start : end + 1])


def judge_case(case: dict, answer: str, tools: list[str]) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
    prompt = (
        f"用户问题：{case['turns']}\n"
        f"参考要点：{case.get('reference') or '无'}\n"
        f"工具调用：{tools}\n"
        f"Agent 回复：{answer}\n\n"
        "请按四个维度打分，只输出 JSON。"
    )
    kwargs = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    try:
        response = client.chat.completions.create(
            **kwargs, response_format={"type": "json_object"}
        )
    except Exception:
        # 有些兼容接口不支持 response_format，退化成纯文本再解析。
        response = client.chat.completions.create(**kwargs)
    data = _extract_json(response.choices[0].message.content or "")
    scores = {}
    for key in DIMENSIONS:
        try:
            scores[key] = max(1, min(5, int(data[key])))
        except (KeyError, TypeError, ValueError):
            scores[key] = 0
    scores["reason"] = str(data.get("reason") or "")
    return scores


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="端到端 Agent 评测")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "evals" / "agent_cases.json",
        help="评测用例（JSON）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evals" / "agent_report.json",
        help="评测报告输出路径",
    )
    parser.add_argument("--case", nargs="+", help="只跑指定 id 的用例")
    parser.add_argument("--limit", type=int, help="只跑前 N 条")
    parser.add_argument("--judge", action="store_true", help="调用 LLM-as-Judge 四维打分")
    parser.add_argument(
        "--dry-run", action="store_true", help="只校验数据集和数据库，不调用大模型"
    )
    args = parser.parse_args()

    cases = load_cases(args.dataset)
    if args.case:
        wanted = set(args.case)
        cases = [case for case in cases if case["id"] in wanted]
        if not cases:
            raise SystemExit(f"没有匹配的用例 id：{sorted(wanted)}")
    if args.limit:
        cases = cases[: args.limit]

    reset_database()
    student_id = seed_database()
    print(f"eval database: {_safe_database_url(EVAL_DATABASE_URL)}")
    print(f"cases        : {len(cases)}")

    if args.dry_run:
        for case in cases:
            print(f"  - {case['id']}: {case['turns']}")
        print("dry run: 数据库已就绪，未调用大模型。")
        return

    results = []
    for case in cases:
        reset_reservations(student_id, bool(case.get("seed_reservation")))
        run = asyncio.run(run_case(student_id, case))
        count = count_reservations()

        tools_ok = check_tools(case, run["tool_calls"])
        answer_ok = check_answer(case, run["answer"])
        reservation_ok = count == case.get("expected_reservation_count", 0)
        passed = tools_ok and answer_ok and reservation_ok and not run["errors"]

        judge = None
        if args.judge:
            try:
                judge = judge_case(case, run["answer"], run["tool_calls"])
            except Exception as exc:
                judge = {"error": str(exc)}

        result = {
            "id": case["id"],
            "turns": case["turns"],
            "answer": run["answer"],
            "tool_calls": run["tool_calls"],
            "errors": run["errors"],
            "expected_tools": case.get("expected_tools", []),
            "expected_any_tools": case.get("expected_any_tools", []),
            "forbidden_tools": case.get("forbidden_tools", []),
            "tools_ok": tools_ok,
            "answer_ok": answer_ok,
            "reservation_count": count,
            "expected_reservation_count": case.get("expected_reservation_count", 0),
            "reservation_ok": reservation_ok,
            "passed": passed,
            "judge": judge,
        }
        results.append(result)

        mark = "PASS" if passed else "FAIL"
        print(
            f"[{mark}] {case['id']:<24} tools={'OK' if tools_ok else 'NG'} "
            f"answer={'OK' if answer_ok else 'NG'} "
            f"db={count}/{case.get('expected_reservation_count', 0)}"
        )
        if not passed:
            print(f"       tools={run['tool_calls']} errors={run['errors']}")
            print(f"       answer={run['answer'][:160]!r}")

    total = len(results)
    passed = sum(1 for item in results if item["passed"])
    print()
    print(f"overall pass : {passed}/{total} ({passed / total:.1%})")
    print(f"tool accuracy: {sum(item['tools_ok'] for item in results)}/{total}")
    print(f"answer pass  : {sum(item['answer_ok'] for item in results)}/{total}")
    print(f"db pass      : {sum(item['reservation_ok'] for item in results)}/{total}")

    judged = [item["judge"] for item in results if item.get("judge") and "error" not in item["judge"]]
    if judged:
        print()
        for key in DIMENSIONS:
            print(f"judge {key:<13}: {average([item[key] for item in judged]):.2f}")
        print(
            "judge overall  : "
            f"{average([average([item[key] for key in DIMENSIONS]) for item in judged]):.2f}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": str(args.dataset),
        "eval_database": _safe_database_url(EVAL_DATABASE_URL),
        "cases": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "tool_accuracy": sum(item["tools_ok"] for item in results) / total if total else 0.0,
        "answer_pass_rate": sum(item["answer_ok"] for item in results) / total if total else 0.0,
        "db_pass_rate": sum(item["reservation_ok"] for item in results) / total if total else 0.0,
        "judge_average": (
            {
                key: average([item[key] for item in judged]) for key in DIMENSIONS
            }
            if judged
            else None
        ),
        "results": results,
    }
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nreport written to {args.output}")


if __name__ == "__main__":
    main()
