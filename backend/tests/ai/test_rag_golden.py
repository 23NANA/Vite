"""RAG 黄金问题集。

默认跳过：首次运行会加载/下载 embedding 模型，耗时且依赖网络。
本地验证时执行：

    RUN_RAG_TESTS=1 python -m pytest tests/ai/test_rag_golden.py -v
"""

from __future__ import annotations

import os

import pytest

from app.services import kb_service

pytestmark = [
    pytest.mark.ai,
    pytest.mark.skipif(
        not os.getenv("RUN_RAG_TESTS"),
        reason="设置 RUN_RAG_TESTS=1 后才运行（需要 embedding 模型）",
    ),
]


@pytest.mark.parametrize(
    ("query", "expected_source"),
    [
        ("预约规则是什么，待审核的预约能取消吗", "预约规则.md"),
        ("实验室的安全规范有哪些", "安全规范.md"),
        ("设备使用前要检查什么", "设备使用.md"),
        ("实验室开放时间", "开放时间.md"),
    ],
)
def test_kb_search_hits_expected_source(query, expected_source):
    result = kb_service.search(query)
    assert result, f"查询没有召回任何内容：{query}"
    assert expected_source in result
