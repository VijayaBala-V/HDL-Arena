import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from vcd_analyzer import parse_vcd
from failure_analyzer import analyze_failures
from source_validator import validate_rtl_submission

SECURITY_TOKENS = (
    "$system",
    "$fopen",
    "$fwrite",
    "$fdisplay",
    "$readmemh",
    "$readmemb",
    "`include",
)

# In-memory cache for golden reference VCDs: (problem_id, test_mode) -> vcd_string
GOLDEN_WAVEFORM_CACHE = {}


def generate_golden_waveform(problem, timeout=12, test_mode="full"):
    """
    Compiles and simulates the trusted reference canonical RTL with the problem's
    testbench to generate a 100% genuine cycle-accurate Golden Waveform VCD.
    Results are cached in memory per (problem_id, test_mode) for zero subsequent latency.
    """
    problem_id = problem.get("id", "unknown")
    cache_key = (problem_id, test_mode)
    if cache_key in GOLDEN_WAVEFORM_CACHE:
        return GOLDEN_WAVEFORM_CACHE[cache_key]

    solution_obj = problem.get("solution") or {}
    canonical_files = solution_obj.get("canonical_code")
    if not canonical_files or not isinstance(canonical_files, dict):
        return ""

    tb_code = problem.get("testbench")
    if not tb_code:
        return ""

    try:
        with tempfile.TemporaryDirectory(prefix="hdl_golden_") as temp:
            workdir = Path(temp)
            ref_paths = []
            for fname, content in canonical_files.items():
                safe_name = Path(fname).name
                target_path = workdir / safe_name
                target_path.write_text(content, encoding="utf-8")
                ref_paths.append(str(target_path))

            tb_file = workdir / "tb.sv"
            tb_file.write_text(tb_code, encoding="utf-8")
            sim_out = workdir / "golden_sim.out"

            compile_cmd = [
                "iverilog",
                "-g2012",
                "-Wall",
                "-s", "tb",
                "-o", str(sim_out),
                *ref_paths,
                str(tb_file)
            ]

            compiled = subprocess.run(
                compile_cmd,
                cwd=temp,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout
            )
            if compiled.returncode != 0:
                return ""

            sim_cmd = ["vvp", str(sim_out)]
            if test_mode == "sample":
                sim_cmd.append("+SAMPLE_ONLY")

            simulated = subprocess.run(
                sim_cmd,
                cwd=temp,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout
            )
            vcd_file = workdir / "wave.vcd"
            if vcd_file.exists():
                golden_vcd = vcd_file.read_text(encoding="utf-8", errors="replace")
                GOLDEN_WAVEFORM_CACHE[cache_key] = golden_vcd
                return golden_vcd
    except Exception as e:
        print(f"Warning: Failed to generate golden waveform: {e}")
        return ""

    return ""


def parse_compiler_diagnostics(clean_err: str, workdir: Path = None):
    """
    Parses Icarus Verilog error output into structured diagnostics:
    file, line, col, message, severity.
    """
    diagnostics = []
    for raw_line in clean_err.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Pattern: filename.v:line[:col]: (error|warning|syntax error): message
        match = re.match(r'^([^:\s]+):(\d+)(?::(\d+))?:\s*(?:(error|warning|syntax error):)?\s*(.*)$', line, re.IGNORECASE)
        if match:
            fname = match.group(1)
            line_no = int(match.group(2))
            col_no = int(match.group(3)) if match.group(3) else 1
            severity = match.group(4) or "error"
            msg = match.group(5) or line
            diagnostics.append({
                "file": fname,
                "line": line_no,
                "col": col_no,
                "severity": severity.lower(),
                "message": msg,
                "raw": line
            })
    return diagnostics


def run_simulation(problem, files_input, language="verilog", timeout=12, test_mode="full"):
    """
    Multi-file compilation and simulation engine using Icarus Verilog.
    files_input can be a dict: { "file1.v": "...", "file2.v": "..." } or a string.
    test_mode can be 'sample' (visible tests only) or 'full' (all tests including hidden suite).
    Guarantees structured JSON return on all paths (accepted, wrong answer, compile error, runtime error, timeout).
    """
    try:
        # Normalize files to dict
        if isinstance(files_input, str):
            default_name = f"{problem['module_name']}.{'sv' if language == 'systemverilog' else 'v'}"
            files = {default_name: files_input}
        elif isinstance(files_input, dict):
            files = files_input
        else:
            return {
                "verdict": "INTERNAL_JUDGE_ERROR",
                "test_mode": test_mode,
                "message": "Invalid source files format.",
                "console": "Invalid source files format received by judge.",
                "test_results": [],
                "cycle_logs": [],
                "waveform": "",
                "golden_waveform": "",
                "golden_available": False,
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
                "diagnostics": {}
            }

        # Security check across all files
        for fname, content in files.items():
            if not isinstance(content, str):
                continue
            content_lower = content.lower()
            for tok in SECURITY_TOKENS:
                if tok in content_lower:
                    return {
                        "verdict": "COMPILE_ERROR",
                        "test_mode": test_mode,
                        "message": f"Security restriction in {fname}: '{tok}' is prohibited in HDL Arena online submissions.",
                        "console": f"Security restriction in {fname}: '{tok}' is prohibited in HDL Arena online submissions.",
                        "test_results": [],
                        "cycle_logs": [],
                        "waveform": "",
                        "golden_waveform": "",
                        "golden_available": False,
                        "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
                        "diagnostics": {
                            "status": "COMPILE_ERROR",
                            "evidence": [f"Prohibited system directive '{tok}' detected in source."],
                            "recommendations": ["Remove system calls or file access directives."]
                        }
                    }

        # Stage 1: Source Validation (module to endmodule, top module match, balanced blocks)
        expected_top = problem.get("module_name", "")
        is_valid, val_err, declared_modules = validate_rtl_submission(files, expected_top)
        if not is_valid:
            val_err["test_mode"] = test_mode
            val_err["test_results"] = []
            val_err["cycle_logs"] = []
            val_err["waveform"] = ""
            val_err["golden_waveform"] = ""
            val_err["golden_available"] = False
            val_err["console"] = val_err.get("message", "")
            val_err["stats"] = {"passed": 0, "total": 0, "exec_time_ms": 0}
            return val_err

        start_time = time.time()

        with tempfile.TemporaryDirectory(prefix="hdl_arena_") as temp:
            workdir = Path(temp)
            user_source_paths = []

            # Write all user files
            for fname, content in files.items():
                safe_name = Path(fname).name
                target_path = workdir / safe_name
                target_path.write_text(content, encoding="utf-8")
                user_source_paths.append(str(target_path))

            # Write problem testbench
            tb_file = workdir / "tb.sv"
            tb_file.write_text(problem["testbench"], encoding="utf-8")
            sim_out = workdir / "sim.out"

            # Stage 2: Compilation Stage with SystemVerilog 2012 support and warnings
            compile_cmd = [
                "iverilog",
                "-g2012",
                "-Wall",
                "-s", "tb",
                "-o", str(sim_out),
                *user_source_paths,
                str(tb_file)
            ]

            try:
                compiled = subprocess.run(
                    compile_cmd,
                    cwd=temp,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=timeout
                )
            except (FileNotFoundError, PermissionError):
                return {
                    "verdict": "INTERNAL_JUDGE_ERROR",
                    "test_mode": test_mode,
                    "message": "Icarus Verilog ('iverilog' / 'vvp') was not found in system PATH or execution permission was denied.",
                    "console": "Compiler binary 'iverilog' could not be executed on host.",
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
                    "diagnostics": {
                        "status": "INTERNAL_JUDGE_ERROR",
                        "evidence": ["Compiler binary was not found or has restricted execution."],
                        "recommendations": ["Ensure Icarus Verilog is installed on the host system."]
                    }
                }
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "TIME_LIMIT_EXCEEDED",
                    "test_mode": test_mode,
                    "message": f"Compilation timed out after {timeout} seconds.",
                    "console": f"Compilation timed out after {timeout} seconds.",
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": timeout * 1000},
                    "diagnostics": {
                        "status": "TIME_LIMIT_EXCEEDED",
                        "evidence": ["Compiler exceeded maximum elaboration time."],
                        "recommendations": ["Check for cyclic includes or macro recursion."]
                    }
                }
            except Exception as comp_err:
                return {
                    "verdict": "INTERNAL_JUDGE_ERROR",
                    "test_mode": test_mode,
                    "message": f"Compilation process error: {str(comp_err)}",
                    "console": str(comp_err),
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
                    "diagnostics": {
                        "status": "INTERNAL_JUDGE_ERROR",
                        "evidence": [str(comp_err)],
                        "recommendations": ["Check submission source code."]
                    }
                }

            # Handle Compilation Errors
            if compiled.returncode != 0:
                clean_err = (compiled.stderr or compiled.stdout or "Compilation failed.").replace(str(workdir) + "/", "")
                compiler_diags = parse_compiler_diagnostics(clean_err, workdir)
                actual_errors = [d for d in compiler_diags if d.get("severity") in ("error", "syntax error")]
                target_diag = actual_errors[0] if actual_errors else (compiler_diags[0] if compiler_diags else None)
                first_err_line = target_diag["line"] if target_diag else 1
                first_err_file = target_diag["file"] if target_diag else (list(files.keys())[0] if files else "source.v")

                try:
                    diag_obj = analyze_failures("COMPILE_ERROR", clean_err, "", [], [], None)
                except Exception:
                    diag_obj = {"status": "COMPILE_ERROR", "evidence": [clean_err], "recommendations": ["Fix syntax errors highlighted in compiler output."]}

                diag_obj["compiler_diagnostics"] = compiler_diags
                diag_obj["error_line"] = first_err_line
                diag_obj["error_file"] = first_err_file

                return {
                    "verdict": "COMPILE_ERROR",
                    "test_mode": test_mode,
                    "message": clean_err[-5000:] or "Compilation failed.",
                    "console": clean_err[-5000:],
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "compiler_diagnostics": compiler_diags,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": round((time.time() - start_time) * 1000, 1)},
                    "diagnostics": diag_obj
                }

            # Stage 3: Simulation Stage
            sim_cmd = ["vvp", str(sim_out)]
            if test_mode == "sample":
                sim_cmd.append("+SAMPLE_ONLY")

            try:
                simulated = subprocess.run(
                    sim_cmd,
                    cwd=temp,
                    capture_output=True,
                    text=True,
                    errors="replace",
                    timeout=timeout
                )
            except (FileNotFoundError, PermissionError):
                return {
                    "verdict": "INTERNAL_JUDGE_ERROR",
                    "test_mode": test_mode,
                    "message": "Icarus Verilog simulator runtime ('vvp') was not found in system PATH or execution was denied.",
                    "console": "Missing or non-executable vvp runtime binary.",
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": round((time.time() - start_time) * 1000, 1)},
                    "diagnostics": {
                        "status": "INTERNAL_JUDGE_ERROR",
                        "evidence": ["Icarus Verilog vvp runtime could not be invoked."],
                        "recommendations": ["Ensure vvp is available in system PATH."]
                    }
                }
            except subprocess.TimeoutExpired:
                return {
                    "verdict": "TIME_LIMIT_EXCEEDED",
                    "test_mode": test_mode,
                    "message": f"Simulation timed out after {timeout} seconds. Check for infinite loops in combinational always blocks.",
                    "console": f"Simulation timed out after {timeout} seconds.",
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": timeout * 1000},
                    "diagnostics": {
                        "status": "TIME_LIMIT_EXCEEDED",
                        "evidence": ["Simulation execution clock hung or loop failed to advance time."],
                        "recommendations": ["Ensure all 'always' blocks have proper sensitivity lists or non-blocking clock progression."]
                    }
                }
            except Exception as sim_err:
                return {
                    "verdict": "INTERNAL_JUDGE_ERROR",
                    "test_mode": test_mode,
                    "message": f"Simulator execution error: {str(sim_err)}",
                    "console": str(sim_err),
                    "test_results": [],
                    "cycle_logs": [],
                    "waveform": "",
                    "golden_waveform": "",
                    "golden_available": False,
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
                    "diagnostics": {
                        "status": "INTERNAL_JUDGE_ERROR",
                        "evidence": [str(sim_err)],
                        "recommendations": ["Check RTL code and resubmit."]
                    }
                }

            exec_time_ms = round((time.time() - start_time) * 1000, 1)
            raw_logs = (simulated.stdout or "") + (simulated.stderr or "")

            # Stage 4: Waveform Processing (Your Wave)
            vcd_file = workdir / "wave.vcd"
            raw_vcd = ""
            vcd_metadata = None
            if vcd_file.exists():
                try:
                    raw_vcd = vcd_file.read_text(encoding="utf-8", errors="replace")
                    vcd_metadata = parse_vcd(raw_vcd)
                except Exception as vcd_err:
                    print(f"Warning: VCD parsing failed: {vcd_err}")
                    raw_vcd = ""
                    vcd_metadata = None

            # Stage 5: Parse Structured Test & Cycle Outputs
            test_results = []
            cycle_logs = []
            clean_console = []

            for line in raw_logs.splitlines():
                if line.startswith("::TEST::"):
                    parts = line.split("::")
                    # Format: ::TEST::<id>::<name>::<status>::<detail>::<time_ns>::<is_hidden>
                    if len(parts) >= 5:
                        t_id = parts[2]
                        t_name = parts[3]
                        t_status = parts[4]
                        t_detail = parts[5] if len(parts) > 5 else ""
                        t_time_str = parts[6] if len(parts) > 6 else "0ns"
                        t_time_num = int(re.sub(r'\D', '', t_time_str) or 0)
                        t_hidden = (parts[7] == "1") if len(parts) > 7 else False

                        test_results.append({
                            "id": t_id,
                            "name": t_name,
                            "status": t_status,
                            "detail": t_detail,
                            "time_ns": t_time_num,
                            "time_str": t_time_str,
                            "is_hidden": t_hidden
                        })
                elif line.startswith("::CYCLE::"):
                    raw_data = line.replace("::CYCLE::", "").strip()
                    cycle_dict = {}
                    tokens = [item.strip() for item in raw_data.split("::") if item.strip()]
                    is_kv = any("=" in item for item in tokens)
                    if is_kv:
                        for item in tokens:
                            if "=" in item:
                                k, v = item.split("=", 1)
                                cycle_dict[k.strip()] = v.strip()
                            elif item.startswith("time") or item.endswith("ns") or item.isdigit():
                                cycle_dict["time"] = item
                    else:
                        if len(tokens) >= 5:
                            if tokens[-1].endswith("ns") or tokens[-1].isdigit() or tokens[-1].startswith("time"):
                                cycle_dict["inputs"] = tokens[0]
                                cycle_dict["expected"] = tokens[1]
                                cycle_dict["actual"] = tokens[2]
                                cycle_dict["match"] = tokens[3]
                                cycle_dict["time"] = tokens[4]
                            else:
                                cycle_dict["time"] = tokens[0]
                                cycle_dict["inputs"] = tokens[1]
                                cycle_dict["expected"] = tokens[2]
                                cycle_dict["actual"] = tokens[3]
                                cycle_dict["match"] = tokens[4]
                        elif len(tokens) >= 4:
                            cycle_dict["inputs"] = tokens[0]
                            cycle_dict["expected"] = tokens[1]
                            cycle_dict["actual"] = tokens[2]
                            cycle_dict["match"] = tokens[3]

                    try:
                        raw_t_val = cycle_dict.get("time_num") or cycle_dict.get("time") or "0"
                        t_num = int(re.sub(r'\D', '', str(raw_t_val)) or 0)
                    except Exception:
                        t_num = 0

                    t_str = cycle_dict.get("time", "")
                    if not t_str or t_str == "time" or t_str.startswith("time="):
                        t_str = f"{t_num}ns"

                    match_raw = str(cycle_dict.get("match", "0")).strip().lower()
                    match_bool = match_raw in ("1", "true", "passed")

                    cycle_logs.append({
                        "time": t_str,
                        "time_num": t_num,
                        "inputs": cycle_dict.get("inputs", ""),
                        "expected": cycle_dict.get("expected", ""),
                        "actual": cycle_dict.get("actual", ""),
                        "match": match_bool
                    })
                elif line.startswith("::ALL_PASSED::"):
                    continue
                else:
                    clean_console.append(line)

            # Stage 6: Verdict Aggregation
            has_explicit_fail = any(t["status"] == "FAILED" for t in test_results)
            passed_count = sum(1 for t in test_results if t["status"] == "PASSED")
            total_count = len(test_results)
            all_passed = (simulated.returncode == 0) and (total_count > 0) and (passed_count == total_count) and (not has_explicit_fail)

            if all_passed:
                verdict = "ACCEPTED"
                summary_msg = f"{'Sample Run Passed' if test_mode == 'sample' else 'Accepted'} — {passed_count}/{total_count} test cases passed ({exec_time_ms} ms)"
            elif simulated.returncode != 0 and total_count == 0:
                verdict = "RUNTIME_ERROR"
                summary_msg = f"Runtime Error — Simulator exited with code {simulated.returncode}."
            else:
                verdict = "WRONG_ANSWER"
                summary_msg = f"Wrong Answer — {passed_count}/{total_count} test cases passed."

            # Stage 7: Generate Real Golden Waveform from Reference Model
            try:
                golden_vcd = generate_golden_waveform(problem, timeout=timeout, test_mode=test_mode)
            except Exception as g_err:
                print(f"Warning: Golden waveform generation failed: {g_err}")
                golden_vcd = ""
            golden_available = bool(golden_vcd and len(golden_vcd) > 0)

            # Stage 8: RTL Diagnostic Failure Analysis
            try:
                diagnostics = analyze_failures(
                    verdict=verdict,
                    compiler_output=compiled.stderr,
                    simulation_logs=raw_logs,
                    test_results=test_results,
                    cycle_logs=cycle_logs,
                    vcd_data=vcd_metadata
                )
            except Exception as diag_err:
                print(f"Warning: Failure analysis error: {diag_err}")
                diagnostics = {
                    "status": verdict,
                    "evidence": [summary_msg],
                    "recommendations": ["Review simulation waveforms and cycle logs."]
                }

            return {
                "verdict": verdict,
                "test_mode": test_mode,
                "message": summary_msg,
                "console": "\n".join(clean_console),
                "test_results": test_results,
                "cycle_logs": cycle_logs,
                "waveform": raw_vcd,
                "golden_waveform": golden_vcd,
                "golden_available": golden_available,
                "vcd_metadata": vcd_metadata,
                "diagnostics": diagnostics,
                "stats": {
                    "passed": passed_count,
                    "total": total_count,
                    "exec_time_ms": exec_time_ms,
                    "returncode": simulated.returncode
                }
            }
    except Exception as unhandled_err:
        import traceback
        traceback.print_exc()
        return {
            "verdict": "INTERNAL_JUDGE_ERROR",
            "test_mode": test_mode,
            "message": f"Simulation engine encountered an error: {str(unhandled_err)}",
            "console": str(unhandled_err),
            "test_results": [],
            "cycle_logs": [],
            "waveform": "",
            "golden_waveform": "",
            "golden_available": False,
            "stats": {"passed": 0, "total": 0, "exec_time_ms": 0},
            "diagnostics": {
                "status": "INTERNAL_JUDGE_ERROR",
                "evidence": [str(unhandled_err)],
                "recommendations": ["Ensure RTL module syntax is valid and try resubmitting."]
            }
        }
