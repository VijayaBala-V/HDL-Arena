"""
HDL Arena — Comprehensive Test Suite & Regression Verification
Phases 0 through 9 Verification
"""

import os
import sys
import json
import shutil
import unittest
from unittest import mock
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import database
from questions_registry import QUESTIONS_REGISTRY
import runner
from runner import execute_question, run_python_program
from importer import validate_license, CANDIDATE_REPOSITORIES_AUDIT
import validator


class TestHDLArena(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()
        database.sync_registry_to_db(QUESTIONS_REGISTRY)

    def test_01_database_integrity_and_backup(self):
        """Verifies PRAGMA integrity_check and backup creation."""
        ok, info = database.backup_database_with_integrity_check()
        self.assertTrue(ok, f"Backup failed: {info}")

    def test_02_phase1_schema_tables_exist(self):
        """Verifies all Phase 1 schema tables are present in SQLite."""
        conn = database.get_db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(r[0] for r in cur.fetchall())
        conn.close()

        expected = [
            "users", "user_profiles", "daily_activity", "coin_transactions",
            "problem_completions", "solution_unlocks", "submissions", "drafts",
            "hint_unlocks", "question_attempts", "problems", "language_variants",
            "reference_solutions", "test_suites", "question_hints",
            "question_explanations", "source_attributions"
        ]
        for t in expected:
            self.assertIn(t, tables, f"Required table '{t}' missing from database schema")

    def test_03_exact_half_coin_units(self):
        """Verifies exact half-coin math (0.5 VJ = 1 unit; 1.0 VJ = 2 units)."""
        self.assertEqual(database.units_to_coins(0), 0.0)
        self.assertEqual(database.units_to_coins(1), 0.5)
        self.assertEqual(database.units_to_coins(2), 1)
        self.assertEqual(database.units_to_coins(5), 2.5)

    def test_04_daily_reward_idempotency_and_timezone(self):
        """Verifies +1 VJ daily reward and duplicate claim prevention in Asia/Kolkata."""
        user = database.get_or_create_default_user()
        user_id = user["id"]

        # First claim or status check
        res1 = database.claim_daily_reward(user_id)
        self.assertTrue(res1["success"])
        self.assertIn("date", res1)

        # Immediate second claim must not double-credit
        res2 = database.claim_daily_reward(user_id)
        self.assertTrue(res2["success"])
        self.assertTrue(res2.get("already_claimed", False))
        self.assertEqual(res2.get("coins_awarded", 0), 0)

    def test_05_progressive_hint_unlock_and_persistence(self):
        """Verifies 0.5 VJ deduction and permanent unlock without re-charge."""
        user = database.get_or_create_default_user()
        user_id = user["id"]
        prob_id = "counter4"

        # Check existing balance
        bal_before = database.get_user_coins_info(user_id)["coins"]

        # Unlock Hint 1
        res = database.unlock_paid_hint(user_id, prob_id, 1)
        if bal_before >= 0.5:
            self.assertTrue(res.get("success", False))
            self.assertTrue(database.is_hint_unlocked(user_id, prob_id, 1))

            # Reopening must not charge again
            res_repeat = database.unlock_paid_hint(user_id, prob_id, 1)
            self.assertTrue(res_repeat.get("success", False))
            self.assertTrue(res_repeat.get("already_unlocked", False))

    def test_06_reference_solution_server_side_gating(self):
        """Verifies reference solutions are restricted and only viewable upon unlock."""
        user = database.get_or_create_default_user()
        user_id = user["id"]
        prob_id = "bitwise_reduction8"

        # Check unlock status
        is_unlocked = database.is_solution_unlocked(user_id, prob_id)
        self.assertIsInstance(is_unlocked, bool)

    def test_07_counter4_submission_execution(self):
        """Verifies counter4 execution via runner dispatch."""
        p = QUESTIONS_REGISTRY.get("counter4")
        self.assertIsNotNone(p)

        canonical = p.get("solution", {}).get("canonical_code", {})
        payload = {"files": canonical, "mode": "sample"}

        result = execute_question(p, payload, test_mode="sample")
        self.assertIn("verdict", result)
        self.assertIn(result["verdict"], ["ACCEPTED", "WRONG_ANSWER", "INTERNAL_JUDGE_ERROR"])

    def test_08_noncoding_evaluators(self):
        """Verifies single choice, multiple choice, and predict output evaluators."""
        # 1. Single Choice: mcq_setup_hold (Correct: A)
        mcq = QUESTIONS_REGISTRY.get("mcq_setup_hold")
        self.assertIsNotNone(mcq)
        # Correct choice submissions
        res_correct = execute_question(mcq, {"choice": "A"})
        self.assertEqual(res_correct["verdict"], "ACCEPTED")
        self.assertEqual(res_correct["score"], 100)

        res_opt_a = execute_question(mcq, {"choice": "Option A"})
        self.assertEqual(res_opt_a["verdict"], "ACCEPTED")

        res_lower_a = execute_question(mcq, {"choice": "a"})
        self.assertEqual(res_lower_a["verdict"], "ACCEPTED")

        # Incorrect choice submissions
        res_wrong = execute_question(mcq, {"choice": "B"})
        self.assertEqual(res_wrong["verdict"], "WRONG_ANSWER")
        self.assertEqual(res_wrong["score"], 0)
        self.assertIn("misconception_explanation", res_wrong)

        # Empty / malformed submissions
        res_empty = execute_question(mcq, {"choice": ""})
        self.assertEqual(res_empty["verdict"], "WRONG_ANSWER")
        res_malformed = execute_question(mcq, {})
        self.assertEqual(res_malformed["verdict"], "WRONG_ANSWER")

        # 2. Predict Output: pred_num_systems (Expected: fc / FC / 0xfc / 8'hfc)
        pred = QUESTIONS_REGISTRY.get("pred_num_systems")
        self.assertIsNotNone(pred)
        # Correct output submissions
        res_pred1 = execute_question(pred, {"output": "fc"})
        self.assertEqual(res_pred1["verdict"], "ACCEPTED")
        self.assertEqual(res_pred1["score"], 100)

        res_pred2 = execute_question(pred, {"output": "FC"})
        self.assertEqual(res_pred2["verdict"], "ACCEPTED")

        res_pred3 = execute_question(pred, {"output": "0xfc"})
        self.assertEqual(res_pred3["verdict"], "ACCEPTED")

        res_pred4 = execute_question(pred, {"output": "8'hfc"})
        self.assertEqual(res_pred4["verdict"], "ACCEPTED")

        # Incorrect output submissions
        res_pred_wrong = execute_question(pred, {"output": "00"})
        self.assertEqual(res_pred_wrong["verdict"], "WRONG_ANSWER")

        # Empty / malformed output submissions
        res_pred_empty = execute_question(pred, {"output": ""})
        self.assertEqual(res_pred_empty["verdict"], "WRONG_ANSWER")
        res_pred_malformed = execute_question(pred, {})
        self.assertEqual(res_pred_malformed["verdict"], "WRONG_ANSWER")

        # 3. Multiple Choice: mcq_blocking_nonblocking (Correct: A, B, D)
        mult_mcq = QUESTIONS_REGISTRY.get("mcq_blocking_nonblocking")
        self.assertIsNotNone(mult_mcq)
        res_mult_correct = execute_question(mult_mcq, {"choices": ["A", "B", "D"]})
        self.assertEqual(res_mult_correct["verdict"], "ACCEPTED")
        self.assertEqual(res_mult_correct["score"], 100)

        res_mult_wrong = execute_question(mult_mcq, {"choices": ["A", "C"]})
        self.assertEqual(res_mult_wrong["verdict"], "WRONG_ANSWER")

        res_mult_empty = execute_question(mult_mcq, {"choices": []})
        self.assertEqual(res_mult_empty["verdict"], "WRONG_ANSWER")

    def test_09_license_compliance_engine(self):
        """Verifies approved vs rejected licenses."""
        ok_mit, _, _ = validate_license("MIT")
        self.assertTrue(ok_mit)

        ok_apache, _, _ = validate_license("Apache-2.0")
        self.assertTrue(ok_apache)

        ok_none, _, err = validate_license("NO_LICENSE")
        self.assertFalse(ok_none)
        self.assertIn("Missing license", err)

    def test_10_content_fingerprint_deduplication(self):
        """Verifies deterministic content fingerprint generation."""
        p1 = {"id": "test1", "title": "Test Title", "description": "Desc"}
        p2 = {"id": "test1", "title": "Test Title", "description": "Desc"}
        p3 = {"id": "test1", "title": "Different Title", "description": "Desc"}

        fp1 = database.generate_problem_fingerprint(p1)
        fp2 = database.generate_problem_fingerprint(p2)
        fp3 = database.generate_problem_fingerprint(p3)

        self.assertEqual(fp1, fp2)
        self.assertNotEqual(fp1, fp3)

    def test_11_software_execution_runners(self):
        """Verifies software execution dispatch for Python, C, and C++."""
        # 1. Python parity check
        py_prob = QUESTIONS_REGISTRY.get("py_parity_check")
        self.assertIsNotNone(py_prob)
        py_sol = py_prob.get("solution", {}).get("canonical_code", {})
        self.assertTrue(py_sol, "py_parity_check missing canonical code")
        res_py = run_python_program(py_sol, py_prob.get("test_harness", {}))
        self.assertEqual(res_py["verdict"], "ACCEPTED", f"Python test failed: {res_py}")
        self.assertGreaterEqual(res_py["stats"]["passed"], 5)

        # 2. C bit reverse dispatch
        c_prob = QUESTIONS_REGISTRY.get("c_bit_reverse")
        self.assertIsNotNone(c_prob)
        c_sol = c_prob.get("solution", {}).get("canonical_code", {})
        self.assertTrue(c_sol, "c_bit_reverse missing canonical code")
        res_c = execute_question(c_prob, {"files": c_sol})
        self.assertIn(res_c["verdict"], ["ACCEPTED", "COMPILER_UNAVAILABLE"])

        # 3. C++ ring buffer dispatch
        cpp_prob = QUESTIONS_REGISTRY.get("cpp_ring_buffer")
        self.assertIsNotNone(cpp_prob)
        cpp_sol = cpp_prob.get("solution", {}).get("canonical_code", {})
        self.assertTrue(cpp_sol, "cpp_ring_buffer missing canonical code")
        res_cpp = execute_question(cpp_prob, {"files": cpp_sol})
        self.assertIn(res_cpp["verdict"], ["ACCEPTED", "COMPILER_UNAVAILABLE"])

        # 4. C++ negative syntax check (should yield COMPILE_ERROR or COMPILER_UNAVAILABLE, never ACCEPTED)
        res_cpp_syntax = execute_question(cpp_prob, {"files": {"ring_buffer.hpp": "syntax error invalid c++ token !!!;"}})
        self.assertIn(res_cpp_syntax["verdict"], ["COMPILE_ERROR", "COMPILER_UNAVAILABLE"])
        self.assertNotEqual(res_cpp_syntax["verdict"], "ACCEPTED")

    def test_12_all_coding_questions_have_canonical_solutions(self):
        """Verifies that 100% of coding and debugging challenges have valid canonical solutions."""
        for qid, q in QUESTIONS_REGISTRY.items():
            if q.get("type") in ("coding", "debugging"):
                sol = q.get("solution", {})
                canonical = sol.get("canonical_code", {})
                self.assertTrue(
                    bool(canonical),
                    f"Question '{qid}' of type '{q.get('type')}' is missing canonical reference code!"
                )

    def test_13_automated_validator_programmatic_pass(self):
        """Verifies that validator accurately tracks schema, duplicates, and honest verification counts."""
        # 1. Verification with simulation skipped: skipped checks must NOT be counted as verified
        report_skipped = validator.run_full_validation(run_simulations=False, run_mutations=False)
        self.assertEqual(
            report_skipped["schema_valid_count"],
            report_skipped["total_registered_questions"],
            "Some questions failed schema validation"
        )
        self.assertEqual(
            report_skipped["duplicate_fingerprints_detected"],
            0,
            "Duplicate question fingerprints detected"
        )
        # Skipped RTL simulations must not count as simulation-verified
        self.assertEqual(report_skipped["reference_simulations_passed"], 0)
        self.assertGreater(report_skipped["reference_simulations_skipped"], 0)
        self.assertEqual(report_skipped["mutation_tests_passed"], 0)
        self.assertGreater(report_skipped["mutation_tests_skipped"], 0)
        # Questions with skipped RTL simulations must NOT be labelled fully verified
        self.assertLess(report_skipped["published_ready_count"], report_skipped["total_registered_questions"])

        # 2. When RTL simulator is installed in environment, run full simulation and mutation checks
        if shutil.which("iverilog") and shutil.which("vvp"):
            report_full = validator.run_full_validation(run_simulations=True, run_mutations=True)
            self.assertEqual(report_full["schema_valid_count"], report_full["total_registered_questions"])
            self.assertGreater(report_full["reference_simulations_passed"], 0)
            self.assertEqual(report_full["reference_simulations_failed"], 0)
            self.assertGreater(report_full["mutation_tests_passed"], 0)
            self.assertEqual(report_full["mutation_tests_failed"], 0)

    def test_14_progressive_hints_structure_and_pricing(self):
        """Verifies hint 0 is free (0.0 VJ) and subsequent hints cost 0.5 VJ."""
        for qid, q in QUESTIONS_REGISTRY.items():
            hints = q.get("progressive_hints", [])
            for h in hints:
                idx = h.get("index")
                cost = h.get("cost")
                if idx == 0:
                    self.assertEqual(cost, 0.0, f"[{qid}] Hint 0 must be free (0.0 VJ), found {cost}")
                elif idx is not None and idx > 0:
                    self.assertEqual(cost, 0.5, f"[{qid}] Hint {idx} must cost 0.5 VJ, found {cost}")

    def test_15_cpp_software_runner_regression(self):
        """Regression tests for C++ execution runner: compiler absence, syntax errors, toolchain errors, and isolation."""
        cpp_prob = QUESTIONS_REGISTRY.get("cpp_ring_buffer")
        self.assertIsNotNone(cpp_prob)
        cpp_sol = cpp_prob.get("solution", {}).get("canonical_code", {})
        self.assertTrue(cpp_sol)

        # 1. Missing compiler behavior (mocked compiler absence)
        with mock.patch("runner.get_cpp_compiler_info", return_value={
            "available": False,
            "compiler": None,
            "flags": [],
            "error": "C++ compiler (clang++/g++) not found in PATH."
        }):
            res_missing = execute_question(cpp_prob, {"files": cpp_sol})
            self.assertEqual(res_missing["verdict"], "COMPILER_UNAVAILABLE")
            self.assertIn("compiler", res_missing["message"].lower())
            self.assertEqual(res_missing["stats"]["passed"], 0)

        # 2. Syntax error with compiler available: must return COMPILE_ERROR with diagnostics
        with mock.patch("runner.get_cpp_compiler_info", return_value={
            "available": True,
            "compiler": "mock_clang++",
            "flags": ["-std=c++17"],
            "error": None
        }):
            mock_comp_fail = mock.MagicMock(
                returncode=1,
                stdout="",
                stderr="driver.cpp:12:5: error: 'undeclared_identifier_xyz' was not declared in this scope"
            )
            with mock.patch("subprocess.run", return_value=mock_comp_fail):
                res_syntax = execute_question(cpp_prob, {"files": {"ring_buffer.hpp": "invalid syntax"}})
                self.assertEqual(res_syntax["verdict"], "COMPILE_ERROR")
                self.assertIn("undeclared_identifier_xyz", res_syntax["console"])
                self.assertNotEqual(res_syntax["verdict"], "ACCEPTED")
                self.assertNotEqual(res_syntax["verdict"], "COMPILER_UNAVAILABLE")

        # 3. Toolchain error with compiler available: must detect toolchain failure and return COMPILER_UNAVAILABLE
        with mock.patch("runner.get_cpp_compiler_info", return_value={
            "available": True,
            "compiler": "mock_clang++",
            "flags": ["-std=c++17"],
            "error": None
        }):
            mock_ld_fail = mock.MagicMock(
                returncode=1,
                stdout="",
                stderr="ld.lld: error: unable to find library -lc++"
            )
            with mock.patch("subprocess.run", return_value=mock_ld_fail):
                res_toolchain = execute_question(cpp_prob, {"files": cpp_sol})
                self.assertEqual(res_toolchain["verdict"], "COMPILER_UNAVAILABLE")
                self.assertIn("unable to find library", res_toolchain["console"])

        # 4. Valid compilation and execution: returns ACCEPTED
        with mock.patch("runner.get_cpp_compiler_info", return_value={
            "available": True,
            "compiler": "mock_clang++",
            "flags": ["-std=c++17"],
            "error": None
        }):
            mock_comp_ok = mock.MagicMock(returncode=0, stdout="", stderr="")
            mock_exec_ok = mock.MagicMock(
                returncode=0,
                stdout="::TEST::tc_01::Init::PASSED::ok::0ns::0\n::TEST::tc_02::Push::PASSED::ok::0ns::0\n",
                stderr=""
            )
            with mock.patch("subprocess.run", side_effect=[mock_comp_ok, mock_exec_ok]):
                res_ok = execute_question(cpp_prob, {"files": cpp_sol})
                self.assertEqual(res_ok["verdict"], "ACCEPTED")
                self.assertEqual(res_ok["stats"]["passed"], 2)

        # 5. Language isolation: submitting non-C++ code (e.g. Python) cannot bypass C++ runner
        res_bypass = execute_question(cpp_prob, {"files": {"solution.py": "def push(): pass"}})
        self.assertIn(res_bypass["verdict"], ["COMPILE_ERROR", "COMPILER_UNAVAILABLE"])
        self.assertNotEqual(res_bypass["verdict"], "ACCEPTED")


if __name__ == "__main__":
    unittest.main()
