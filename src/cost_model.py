# -*- coding: utf-8 -*-
"""单个成功任务成本模型。

产品评审里最常见的错误，是拿「单次模型调用单价」当成本口径。
便宜模型如果成功率低、要反复重试、还要人工兜底，单个成功任务的成本
可能远高于贵的模型。这里把重试、缓存、工具开销和人工兜底都算进去。

所有金额单位由调用方统一（示例用人民币元），函数不假设币种。
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CostInputs:
    price_per_call: float          # 一次模型调用的价格
    calls_per_attempt: float       # 一次尝试内的模型调用次数
    success_rate: float            # 一次尝试的成功率，0 < x <= 1
    cache_hit_rate: float = 0.0    # 命中缓存的比例，命中则不调模型
    tool_cost_per_attempt: float = 0.0   # 检索 / 工具固定开销
    human_fallback_rate: float = 0.0     # 转人工的比例
    human_minutes: float = 0.0           # 每次人工处理耗时（分钟）
    human_hourly_cost: float = 0.0       # 人工小时成本
    label: str = ""


def _validate(i: CostInputs) -> None:
    if i.price_per_call < 0 or i.tool_cost_per_attempt < 0 or i.human_hourly_cost < 0:
        raise ValueError("价格与成本不能为负")
    if i.calls_per_attempt <= 0:
        raise ValueError("calls_per_attempt 必须 > 0")
    if not 0 < i.success_rate <= 1:
        raise ValueError("success_rate 必须在 (0, 1] 区间")
    for name in ("cache_hit_rate", "human_fallback_rate"):
        value = getattr(i, name)
        if not 0 <= value < 1:
            raise ValueError("%s 必须在 [0, 1) 区间" % name)
    if i.human_minutes < 0:
        raise ValueError("human_minutes 不能为负")


def compute(i: CostInputs) -> Dict[str, float]:
    """返回成本拆解与单个成功任务成本 cost_per_success。"""
    _validate(i)
    effective_calls = i.calls_per_attempt * (1 - i.cache_hit_rate)
    model_cost = effective_calls * i.price_per_call
    attempt_cost = model_cost + i.tool_cost_per_attempt
    expected_attempts = 1.0 / i.success_rate
    auto_cost = attempt_cost * expected_attempts
    tool_cost = i.tool_cost_per_attempt * expected_attempts
    model_total = model_cost * expected_attempts
    human_cost = i.human_fallback_rate * (i.human_minutes / 60.0) * i.human_hourly_cost
    return {
        "label": i.label,
        "effective_calls": round(effective_calls, 6),
        "expected_attempts": round(expected_attempts, 6),
        "attempt_cost": round(attempt_cost, 6),
        "model_cost": round(model_total, 6),
        "tool_cost": round(tool_cost, 6),
        "human_cost": round(human_cost, 6),
        "cost_per_success": round(auto_cost + human_cost, 6),
    }


def compare(scenarios: Dict[str, CostInputs]) -> List[Dict[str, float]]:
    """按单个成功任务成本升序返回各方案，供 PRD 里做方案对比。"""
    rows = []
    for name, inputs in scenarios.items():
        if not inputs.label:
            inputs = CostInputs(**{**inputs.__dict__, "label": name})
        rows.append(compute(inputs))
    return sorted(rows, key=lambda row: row["cost_per_success"])
