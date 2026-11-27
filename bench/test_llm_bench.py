"""Unit tests for the benchmark harness, run against the local mock server.

    python -m unittest discover -s bench -v      # or: python -m pytest bench
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import llm_bench  # noqa: E402
from mock_server import make_server  # noqa: E402

TTFT_S = 0.05
ITL_S = 0.01


class _ServerCase(unittest.TestCase):
    fail_every = 0

    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0, ttft=TTFT_S, itl=ITL_S, fail_every=cls.fail_every)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def args(self, *extra):
        return llm_bench.parse_args(
            ["--base-url", self.base_url, "--model", "mock", "--input-len", "64", "--output-len", "20",
             "--warmup", "0", *extra]
        )


class TestHelpers(unittest.TestCase):
    def test_percentile_matches_linear_interpolation(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(llm_bench.percentile(data, 0), 1)
        self.assertEqual(llm_bench.percentile(data, 100), 10)
        self.assertAlmostEqual(llm_bench.percentile(data, 50), 5.5)
        self.assertAlmostEqual(llm_bench.percentile(data, 90), 9.1)
        self.assertIsNone(llm_bench.percentile([], 50))
        self.assertEqual(llm_bench.percentile([3.0], 99), 3.0)

    def test_build_prompt_length_and_determinism(self):
        p = llm_bench.build_prompt(128, seed=3)
        self.assertEqual(len(p.split()), 128)
        self.assertEqual(p, llm_bench.build_prompt(128, seed=3))
        self.assertNotEqual(p, llm_bench.build_prompt(128, seed=4))
        with self.assertRaises(ValueError):
            llm_bench.build_prompt(0, seed=0)

    def test_tpot_definition(self):
        r = llm_bench.RequestResult(ok=True, ttft_ms=100.0, e2e_ms=1100.0, output_tokens=11)
        self.assertAlmostEqual(r.tpot_ms, 100.0)
        self.assertIsNone(llm_bench.RequestResult(ok=True, ttft_ms=1, e2e_ms=2, output_tokens=1).tpot_ms)
        self.assertIsNone(llm_bench.RequestResult(ok=False).tpot_ms)

    def test_parse_concurrency(self):
        a = llm_bench.parse_args(["--base-url", "http://x/v1", "--model", "m"])
        self.assertEqual(a.concurrency_levels, [1, 8, 32, 64])
        with self.assertRaises(SystemExit):
            llm_bench.parse_args(["--base-url", "http://x/v1", "--model", "m", "--concurrency", "0"])


class TestAgainstMock(_ServerCase):
    def test_single_request_chat(self):
        r = llm_bench.send_request(self.args(), "hello world")
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.output_tokens, 20)
        self.assertEqual(r.prompt_tokens, 2)
        self.assertEqual(len(r.itl_ms), 19)
        self.assertGreaterEqual(r.ttft_ms, TTFT_S * 1000 * 0.9)
        self.assertGreaterEqual(r.tpot_ms, ITL_S * 1000 * 0.9)
        self.assertLess(r.tpot_ms, ITL_S * 1000 * 5)

    def test_single_request_completions_endpoint(self):
        r = llm_bench.send_request(self.args("--endpoint", "completions"), "hello")
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.output_tokens, 20)

    def test_levels_metrics_and_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "run")
            rc = llm_bench.main(
                ["--base-url", self.base_url, "--model", "mock", "--input-len", "32", "--output-len", "10",
                 "--concurrency", "1,8", "--num-requests", "8", "--warmup", "1", "--label", "unit", "--out", out]
            )
            self.assertEqual(rc, 0)
            with open(out + ".json", encoding="utf-8") as f:
                report = json.load(f)
            with open(out + ".md", encoding="utf-8") as f:
                md = f.read()
        self.assertEqual([r["concurrency"] for r in report["results"]], [1, 8])
        c1, c8 = report["results"]
        for r in (c1, c8):
            self.assertEqual(r["completed"], 8)
            self.assertEqual(r["failed"], 0)
            self.assertEqual(r["mean_output_tokens"], 10)
            self.assertEqual(r["mean_prompt_tokens"], 32)
            for key in ("ttft_ms", "tpot_ms", "itl_ms", "e2e_ms"):
                self.assertIsNotNone(r[key]["p50"], key)
        # The mock serves requests in parallel, so 8-way concurrency must beat serial.
        self.assertGreater(c8["output_throughput_tok_s"], c1["output_throughput_tok_s"] * 2)
        self.assertGreater(c8["request_throughput_rps"], c1["request_throughput_rps"] * 2)
        self.assertIn("| Concurrency |", md)
        self.assertIn("| 8 | 8/8 |", md)
        self.assertEqual(report["meta"]["label"], "unit")

    def test_concurrency_64_no_failures(self):
        res = llm_bench.run_level(self.args("--output-len", "5", "--num-requests", "128"), concurrency=64)
        self.assertEqual(res["failed"], 0, res["errors"])
        self.assertEqual(res["completed"], 128)

    def test_unreachable_server_counts_failure(self):
        a = llm_bench.parse_args(["--base-url", "http://127.0.0.1:9/v1", "--model", "m", "--timeout", "2"])
        r = llm_bench.send_request(a, "x")
        self.assertFalse(r.ok)
        self.assertIsNotNone(r.error)


class TestFailures(_ServerCase):
    fail_every = 2  # every second request returns HTTP 500

    def test_http_errors_are_reported_and_exit_code_nonzero(self):
        res = llm_bench.run_level(self.args("--num-requests", "6"), concurrency=1)
        self.assertEqual(res["num_requests"], 6)
        self.assertEqual(res["failed"], 3)
        self.assertEqual(res["completed"], 3)
        self.assertTrue(any("500" in e for e in res["errors"]))
        rc = llm_bench.main(["--base-url", self.base_url, "--model", "mock", "--input-len", "8",
                             "--output-len", "4", "--concurrency", "1", "--num-requests", "4", "--warmup", "0"])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
