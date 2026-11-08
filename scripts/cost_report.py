# -*- coding: utf-8 -*-
"""三种方案的单个成功任务成本对比，输出 Markdown 表与 results/cost_report.json。"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.cost_model import CostInputs, compare  # noqa: E402

SCENARIOS = {
    "全用强模型": CostInputs(
        price_per_call=0.060, calls_per_attempt=1.0, success_rate=0.72,
        human_fallback_rate=0.15, human_minutes=6, human_hourly_cost=90,
        label="全用强模型"),
    "模型分层 + 缓存": CostInputs(
        price_per_call=0.012, calls_per_attempt=1.4, success_rate=0.80,
        cache_hit_rate=0.35, tool_cost_per_attempt=0.001,
        human_fallback_rate=0.10, human_minutes=5, human_hourly_cost=90,
        label="模型分层 + 缓存"),
    "分层 + 缓存 + 工具兜底": CostInputs(
        price_per_call=0.012, calls_per_attempt=1.4, success_rate=0.88,
        cache_hit_rate=0.45, tool_cost_per_attempt=0.002,
        human_fallback_rate=0.05, human_minutes=4, human_hourly_cost=90,
        label="分层 + 缓存 + 工具兜底"),
}


def main():
    rows = compare(SCENARIOS)
    out = os.path.join(ROOT, "results", "cost_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)

    print("| 方案 | 单个成功任务成本 | 期望尝试次数 | 模型成本 | 工具成本 | 人工成本 |")
    print("| --- | --- | --- | --- | --- | --- |")
    for row in rows:
        print("| %s | %.4f | %.2f | %.4f | %.4f | %.4f |" % (
            row["label"], row["cost_per_success"], row["expected_attempts"],
            row["model_cost"], row["tool_cost"], row["human_cost"]))
    print("\n cheapest = %s" % rows[0]["label"])
    print("结果写入 results/cost_report.json")
    return rows


if __name__ == "__main__":
    main()
