# -*- coding: utf-8 -*-
"""成本模型的单调性、边界与对比排序测试。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.cost_model import CostInputs, compare, compute  # noqa: E402


class TestCompute(unittest.TestCase):
    def test_basic(self):
        row = compute(CostInputs(price_per_call=0.1, calls_per_attempt=2,
                                 success_rate=0.5, label="x"))
        self.assertAlmostEqual(row["expected_attempts"], 2.0)
        self.assertAlmostEqual(row["model_cost"], 0.4)
        self.assertAlmostEqual(row["cost_per_success"], 0.4)

    def test_cache_reduces_cost(self):
        base = CostInputs(price_per_call=0.1, calls_per_attempt=2, success_rate=0.8)
        cached = CostInputs(price_per_call=0.1, calls_per_attempt=2,
                            success_rate=0.8, cache_hit_rate=0.5)
        self.assertLess(compute(cached)["cost_per_success"],
                        compute(base)["cost_per_success"])

    def test_cheap_model_can_cost_more(self):
        """口径验证：单价便宜但成功率低时，单个成功任务反而更贵。"""
        cheap = CostInputs(price_per_call=0.01, calls_per_attempt=1,
                           success_rate=0.12)
        strong = CostInputs(price_per_call=0.06, calls_per_attempt=1,
                            success_rate=0.95)
        self.assertGreater(compute(cheap)["cost_per_success"],
                           compute(strong)["cost_per_success"])

    def test_human_fallback_adds_cost(self):
        base = CostInputs(price_per_call=0.02, calls_per_attempt=1, success_rate=0.9)
        with_human = CostInputs(price_per_call=0.02, calls_per_attempt=1,
                                success_rate=0.9, human_fallback_rate=0.2,
                                human_minutes=6, human_hourly_cost=90)
        self.assertAlmostEqual(compute(with_human)["human_cost"], 1.8)
        self.assertGreater(compute(with_human)["cost_per_success"],
                           compute(base)["cost_per_success"])

    def test_breakdown_sums(self):
        row = compute(CostInputs(price_per_call=0.03, calls_per_attempt=1.5,
                                 success_rate=0.75, cache_hit_rate=0.2,
                                 tool_cost_per_attempt=0.002,
                                 human_fallback_rate=0.1, human_minutes=3,
                                 human_hourly_cost=60))
        self.assertAlmostEqual(row["model_cost"] + row["tool_cost"]
                               + row["human_cost"], row["cost_per_success"],
                               places=5)


class TestValidation(unittest.TestCase):
    def test_invalid_rates(self):
        for kwargs in ({"success_rate": 0}, {"success_rate": 1.5},
                       {"cache_hit_rate": 1.0}, {"cache_hit_rate": -0.1},
                       {"human_fallback_rate": 1.0}):
            with self.subTest(kwargs=kwargs):
                base = dict(price_per_call=0.1, calls_per_attempt=1, success_rate=0.8)
                base.update(kwargs)
                with self.assertRaises(ValueError):
                    compute(CostInputs(**base))

    def test_negative_price(self):
        with self.assertRaises(ValueError):
            compute(CostInputs(price_per_call=-1, calls_per_attempt=1, success_rate=0.8))


class TestCompare(unittest.TestCase):
    def test_sorted_and_labelled(self):
        rows = compare({"a": CostInputs(0.05, 1, 0.5),
                        "b": CostInputs(0.01, 1, 0.9)})
        self.assertEqual(rows[0]["label"], "b")
        self.assertLess(rows[0]["cost_per_success"], rows[1]["cost_per_success"])


if __name__ == "__main__":
    unittest.main()
