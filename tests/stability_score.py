"""Stability scoring tests.

Validate rule-triggered tool calls and output reports.
"""

import asyncio
import json
import time
from pathlib import Path
from statistics import median
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import (
    MemorySearchInput,
    MemoryAddInput,
    MemorySuggestCategoryInput,
    MemoryListTagsInput,
    MemoryGetProjectContextInput,
)
from tools.memory_search import memory_search
from tools.memory_add import memory_add
from tools.memory_suggest_category import memory_suggest_category
from tools.memory_list_tags import memory_list_tags
from tools.memory_get_project_context import memory_get_project_context

CASE_FILE = project_root / "tests" / "stability_cases.json"
REPORT_DIR = project_root / "test_reports"
REPORT_JSON = REPORT_DIR / "stability_report.json"
REPORT_MD = REPORT_DIR / "stability_report.md"


def latency_score(p95_ms: float) -> float:
    if p95_ms <= 1000:
        return 1.0
    if p95_ms <= 2000:
        return 0.8
    if p95_ms <= 5000:
        return 0.6
    return 0.4


def p95(values):
    if not values:
        return 0.0
    values_sorted = sorted(values)
    idx = int(round(0.95 * (len(values_sorted) - 1)))
    return values_sorted[idx]


async def run_case(case):
    expected_tool = case.get("expected_tool")
    params = case.get("params", {})
    quality_rules = case.get("quality", {})

    if expected_tool == "none":
        return {
            "id": case.get("id"),
            "prompt": case.get("prompt"),
            "expected_tool": expected_tool,
            "status": "skipped",
            "rule_pass": True,
            "quality_pass": True,
            "duration_ms": 0.0,
        }

    tool_start = time.perf_counter()
    result = None

    if expected_tool == "memory_search":
        result_str = await memory_search(MemorySearchInput(**params))
        result = json.loads(result_str)
    elif expected_tool == "memory_add":
        result_str = await memory_add(MemoryAddInput(**params))
        result = json.loads(result_str)
    elif expected_tool == "memory_suggest_category":
        result_str = await memory_suggest_category(MemorySuggestCategoryInput(**params))
        result = json.loads(result_str)
    elif expected_tool == "memory_list_tags":
        result_str = await memory_list_tags(MemoryListTagsInput(**params))
        result = json.loads(result_str)
    elif expected_tool == "memory_get_project_context":
        result_str = await memory_get_project_context(MemoryGetProjectContextInput(**params))
        result = json.loads(result_str)
    else:
        result = {"status": "error", "message": f"Unknown tool: {expected_tool}"}

    duration_ms = (time.perf_counter() - tool_start) * 1000

    status = result.get("status")
    rule_pass = status == "success" or quality_rules.get("allow_error", False)

    quality_pass = True
    if quality_rules.get("require_message_on_empty"):
        if result.get("count", 0) == 0:
            quality_pass = "message" in result and "没有找到" in result.get("message", "")
    if quality_rules.get("require_id"):
        quality_pass = quality_pass and bool(result.get("id"))
    if quality_rules.get("require_confidence"):
        suggestion = result.get("suggestion", {})
        quality_pass = quality_pass and ("confidence" in suggestion)
    if quality_rules.get("require_tags"):
        quality_pass = quality_pass and ("tags" in result)

    return {
        "id": case.get("id"),
        "prompt": case.get("prompt"),
        "expected_tool": expected_tool,
        "status": status,
        "rule_pass": rule_pass,
        "quality_pass": quality_pass,
        "duration_ms": round(duration_ms, 2),
        "result": result,
    }


async def run_all():
    data = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases", [])

    results = []
    durations = []
    rule_passes = 0
    quality_passes = 0

    for case in cases:
        case_result = await run_case(case)
        results.append(case_result)

        if case_result.get("duration_ms"):
            durations.append(case_result["duration_ms"])
        if case_result.get("rule_pass"):
            rule_passes += 1
        if case_result.get("quality_pass"):
            quality_passes += 1

    total = len(cases)
    rule_rate = rule_passes / total if total else 0
    quality_rate = quality_passes / total if total else 0

    p50 = median(durations) if durations else 0.0
    p95_value = p95(durations)
    latency_score_value = latency_score(p95_value)

    overall_score = round((rule_rate * 0.5 + quality_rate * 0.3 + latency_score_value * 0.2) * 100, 2)

    report = {
        "total_cases": total,
        "rule_adherence_rate": round(rule_rate * 100, 2),
        "quality_rate": round(quality_rate * 100, 2),
        "latency_p50_ms": round(p50, 2),
        "latency_p95_ms": round(p95_value, 2),
        "latency_score": round(latency_score_value * 100, 2),
        "overall_score": overall_score,
        "cases": results,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 稳定性评分报告",
        "",
        f"- 总用例数: {total}",
        f"- 规则遵循率: {report['rule_adherence_rate']}%",
        f"- 回答质量通过率: {report['quality_rate']}%",
        f"- 延迟 P50: {report['latency_p50_ms']} ms",
        f"- 延迟 P95: {report['latency_p95_ms']} ms",
        f"- 延迟得分: {report['latency_score']}%",
        f"- 综合得分: {report['overall_score']}%",
        "",
        "## 失败用例",
    ]

    failed = [c for c in results if not (c.get("rule_pass") and c.get("quality_pass"))]
    if not failed:
        lines.append("- 无")
    else:
        for case in failed:
            lines.append(f"- {case['id']}: tool={case['expected_tool']} status={case.get('status')}")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return report


if __name__ == "__main__":
    asyncio.run(run_all())
