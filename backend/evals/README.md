# 离线评测

两个脚本，都在 `backend/` 目录下运行：

| 脚本 | 评什么 | 需要大模型 |
| --- | --- | --- |
| `scripts/eval_rag.py` | 检索命中：Hit@k / Recall@k / MRR@k | 否（只用 embedding 模型） |
| `scripts/eval_agent.py` | 端到端：工具调用、答案要点、真实落库、LLM-as-Judge | 是 |

## 1. RAG 命中率

```bash
.venv/Scripts/python.exe scripts/eval_rag.py --ks 1 2 3 5 --verbose
.venv/Scripts/python.exe scripts/eval_rag.py --json evals/rag_report.json
```

数据集：`evals/rag_golden.jsonl`，每行一个问题：

```json
{"id": "booking-cancel-pending", "query": "待审核的预约可以取消吗", "expected_sources": ["预约规则.md"]}
```

指标口径：

- **Hit@k**：前 k 条里至少命中一篇期望文档。
- **Recall@k**：前 k 条命中的期望文档数 / 该问题的期望文档总数。
- **MRR@k**：第一条命中结果的排名倒数（1/rank），未命中记 0。

> 当前知识库只有 4 篇短文档，Top-5 基本等于全量召回，所以 `Hit@5` 必然是 100%。
> 有区分度的是 `Hit@1` 和 `MRR@3`。想让指标更有说服力，先把 `data/kb/`
> 扩到 30 篇以上，并补充 50 条以上问题；否则不建议把命中率写进简历。

## 2. 端到端 Agent 评测

```bash
# 只校验数据集和数据库，不调用大模型
.venv/Scripts/python.exe scripts/eval_agent.py --dry-run

# 跑真实 Agent（会调用 backend/.env 里的 LLM_API_KEY，产生费用）
.venv/Scripts/python.exe scripts/eval_agent.py

# 加 LLM-as-Judge 四维打分（相关性/准确性/完整性/有用性，各 1-5 分）
.venv/Scripts/python.exe scripts/eval_agent.py --judge

# 只跑前 3 条
.venv/Scripts/python.exe scripts/eval_agent.py --limit 3 --judge

# 只跑指定用例（注意显式指定 --output，避免覆盖全量报告）
.venv/Scripts/python.exe scripts/eval_agent.py --case cancel-boundary --judge \
  --output evals/agent_report_cancel.json
```

数据集：`evals/agent_cases.json`。一条用例长这样：

```json
{
  "id": "book-confirm",
  "turns": ["帮我预约明天上午 9 点到 10 点的云计算实验室", "确认预约"],
  "expected_tools": ["create_lab_reservation"],
  "expected_any_tools": ["get_today", "list_open_labs"],
  "forbidden_tools": [],
  "answer_contains_any": ["提交", "审核", "待审核"],
  "expected_reservation_count": 1,
  "reference": "先复述信息，用户确认后提交；提交后状态为待审核。"
}
```

判定分四层，避免只靠 Judge：

1. **工具调用**：`expected_tools` 必须全部出现，`expected_any_tools` 至少出现一个，`forbidden_tools` 不能出现。
2. **答案要点**：回复必须包含 `answer_contains_any` 中任意一个关键词。
3. **真实落库**：预约数量必须等于 `expected_reservation_count`，防止“嘴上说预约成功但没写库”。
4. **LLM-as-Judge**：可选，四个维度各 1-5 分。

### 数据库隔离

脚本会强制把 `DATABASE_URL` 切到独立的 `lab_agent_eval` 库，并拒绝在库名不以
`_eval` / `_test` 结尾的数据库上运行，避免清空开发库。也可以显式指定：

```bash
EVAL_DATABASE_URL="mysql+pymysql://user:pass@127.0.0.1:3306/lab_agent_eval?charset=utf8mb4" \
  .venv/Scripts/python.exe scripts/eval_agent.py --dry-run
```

### 费用

`--judge` 每条用例会多一次 LLM 调用。11 条用例就是 11 次 Agent 调用 + 11 次 Judge 调用。
建议先用 `--limit 3 --judge` 验证，再跑全量。
