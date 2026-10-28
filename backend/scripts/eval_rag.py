#!/usr/bin/env python
"""RAG 检索命中率评测。

用法（在 backend 目录下）：

    .venv/Scripts/python.exe scripts/eval_rag.py
    .venv/Scripts/python.exe scripts/eval_rag.py --ks 1 3 5 --verbose
    .venv/Scripts/python.exe scripts/eval_rag.py --json evals/rag_report.json

指标口径：
- Hit@k    前 k 条里至少有一条命中期望文档，记 1，否则 0。
- Recall@k 前 k 条命中的期望文档数 / 该问题的期望文档总数。
- MRR@k    第一条命中结果的排名倒数（1/rank），未命中记 0。

注意：当前知识库只有 4 篇短文档，Top-5 基本等于全量召回，
因此 Hit@5 / Recall@5 会接近 100%，真正有区分度的是 Hit@1 和 MRR@3。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import kb_service  # noqa: E402


def load_dataset(path: Path) -> list[dict]:
    cases = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no} 不是合法 JSON: {exc}") from exc
            if not case.get("id") or not case.get("query"):
                raise SystemExit(f"{path}:{line_no} 缺少 id 或 query")
            if not case.get("expected_sources"):
                raise SystemExit(f"{path}:{line_no} 缺少 expected_sources")
            cases.append(case)
    if not cases:
        raise SystemExit(f"{path} 没有可用用例")
    return cases


def score_one(ranked: list[str], expected: list[str], k: int) -> dict:
    expected_set = set(expected)
    top_k = ranked[:k]
    hit_positions = [i for i, source in enumerate(top_k, 1) if source in expected_set]
    return {
        "hit": 1.0 if hit_positions else 0.0,
        "recall": len({top_k[i - 1] for i in hit_positions}) / len(expected_set),
        "rr": 1.0 / hit_positions[0] if hit_positions else 0.0,
    }


def fmt(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 检索命中率评测")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "evals" / "rag_golden.jsonl",
        help="黄金问题集（JSONL）",
    )
    parser.add_argument(
        "--ks",
        type=int,
        nargs="+",
        default=[1, 3, 5],
        help="要计算的 k 列表，默认 1 3 5",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="实际检索深度，默认 5（与线上 search 一致）",
    )
    parser.add_argument("--json", type=Path, help="把逐条结果和汇总写到 JSON 文件")
    parser.add_argument("--verbose", action="store_true", help="打印每条问题的命中情况")
    args = parser.parse_args()

    cases = load_dataset(args.dataset)
    top_k = max(max(args.ks), args.top_k)

    rows = []
    for case in cases:
        results = kb_service.retrieve(case["query"], n_results=top_k)
        ranked = [item["source"] for item in results]
        rows.append(
            {
                "id": case["id"],
                "query": case["query"],
                "expected_sources": case["expected_sources"],
                "ranked_sources": ranked,
                "scores": {
                    item["source"]: round(item["score"], 4) for item in results
                },
            }
        )

    metrics = {}
    for k in args.ks:
        per_row = [score_one(row["ranked_sources"], row["expected_sources"], k) for row in rows]
        metrics[k] = {
            "hit": sum(item["hit"] for item in per_row) / len(per_row),
            "recall": sum(item["recall"] for item in per_row) / len(per_row),
            "mrr": sum(item["rr"] for item in per_row) / len(per_row),
        }

    corpus_docs = kb_service.get_collcetion().count()
    print("RAG retrieval eval")
    print(f"dataset : {args.dataset}")
    print(f"queries : {len(rows)}    corpus_docs: {corpus_docs}    top_k: {top_k}")
    print()
    print(f"{'k':>2}  {'Hit@k':>7}  {'Recall@k':>9}  {'MRR@k':>7}")
    for k in args.ks:
        item = metrics[k]
        print(f"{k:>2}  {fmt(item['hit']):>7}  {fmt(item['recall']):>9}  {fmt(item['mrr']):>7}")

    misses = [row for row in rows if not set(row["ranked_sources"][:1]) & set(row["expected_sources"])]
    print()
    print(f"Top-1 misses: {len(misses)}/{len(rows)}")
    for row in misses:
        print(f"  - {row['id']}: {row['query']}  expected={row['expected_sources']}  ranked={row['ranked_sources']}")

    if args.verbose:
        print()
        for row in rows:
            mark = "OK " if set(row["ranked_sources"][:1]) & set(row["expected_sources"]) else "MISS"
            print(f"[{mark}] {row['id']}  ranked={row['ranked_sources']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "dataset": str(args.dataset),
            "queries": len(rows),
            "corpus_docs": corpus_docs,
            "top_k": top_k,
            "metrics": {str(k): v for k, v in metrics.items()},
            "rows": rows,
        }
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nreport written to {args.json}")


if __name__ == "__main__":
    main()
