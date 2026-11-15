"""
HDL Arena Unified Multi-Language & Multi-Format Evaluation Runner
Supports:
- Languages: Verilog, SystemVerilog, C, C++, Python
- Question Types:
    1. coding (RTL & software execution in sandboxed subdirectories)
    2. single_choice (instant option verification with misconception analysis)
    3. multiple_choice (multi-select verification)
    4. predict_output (exact / normalized radix matching)
    5. fill_in_code (template stitching and compilation)
    6. debugging (bug isolation and test verification)
    7. conceptual (rubric scoring and criteria matching)
    8. interview_scenario (structured multi-dimensional rubric evaluation)
"""

import os
import re
import sys
import time
import shutil
import tempfile
import subprocess
from compiler import run_simulation


def is_toolchain_error(stderr_text: str) -> bool:
    """Detects whether a compiler failure is due to missing toolchain/libraries vs user syntax errors."""
    if not stderr_text:
        return False
    lower = stderr_text.lower()
    toolchain_indicators = [
        "cannot find -l",
        "unable to find library",
        "permission denied",
        "exec format error",
        "unable to execute command",
        "failed to exec",
        "no such file or directory",
        "fatal error: 'iostream' file not found",
        "fatal error: 'cstddef' file not found",
        "fatal error: 'cassert' file not found",
        "fatal error: 'stdio.h' file not found",
        "fatal error: 'stdint.h' file not found",
        "fatal error: 'stdbool.h' file not found",
        "fatal error: 'stddef.h' file not found",
        "fatal error: 'stdlib.h' file not found",
        "iostream: no such file or directory",
        "cassert: no such file or directory",
        "cstddef: no such file or directory",
        "stdio.h: no such file or directory",
        "stdint.h: no such file or directory",
        "stddef.h: no such file or directory",
        "stdlib.h: no such file or directory",
        "bits/c++config.h: no such file or directory",
        "cannot open crt",
        "crtbegin",
        "crtend",
        "linker command failed with exit code",
        "error: command not found",
        "clang: error: linker command failed",
        "clang++: error: linker command failed",
        "ld returned 1 exit status",
        "ld.lld: error:",
        "collect2: error: ld returned",
        "undefined reference to",
        "undefined symbol:",
        "posix_spawn",
        "clang++: error: no input files",
        "clang: error: no input files",
        "g++: error: no input files",
        "gcc: error: no input files",
        "cannot find -lc++",
        "cannot find -lstdc++",
        "cannot find -lm",
        "cannot find -lc",
    ]
    return any(ind in lower for ind in toolchain_indicators)


_C_COMPILER_INFO = None

def get_c_compiler_info():
    """
    Probes and caches C compiler availability and capabilities.
    Returns dict: {'available': bool, 'compiler': str, 'flags': list, 'error': str}
    """
    global _C_COMPILER_INFO
    if _C_COMPILER_INFO is not None:
        return _C_COMPILER_INFO

    c_compiler = shutil.which("clang") or shutil.which("gcc")
    if not c_compiler:
        _C_COMPILER_INFO = {
            "available": False,
            "compiler": None,
            "flags": [],
            "error": "C compiler (clang/gcc) not found in PATH."
        }
        return _C_COMPILER_INFO

    probe_dir = tempfile.mkdtemp(prefix="c_probe_")
    try:
        probe_src = os.path.join(probe_dir, "probe.c")
        probe_bin = os.path.join(probe_dir, "probe.bin")
        with open(probe_src, "w", encoding="utf-8") as f:
            f.write("#include <stdio.h>\n#include <stdint.h>\nint main(void) { printf(\"ok\"); return 0; }\n")

        flag_candidates = [
            ["-O2", "-Wall"],
            ["-O2", "-Wall", "-lm"],
        ]
        chosen_flags = None
        last_err = ""
        for flags in flag_candidates:
            try:
                cmd = [c_compiler] + flags + ["-o", probe_bin, probe_src]
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    errors="replace",
                    timeout=5
                )
                if res.returncode == 0 and os.path.exists(probe_bin):
                    exec_res = subprocess.run(
                        [probe_bin],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        errors="replace",
                        timeout=3
                    )
                    if exec_res.returncode == 0 and "ok" in exec_res.stdout:
                        chosen_flags = flags
                        break
                    else:
                        last_err = (exec_res.stderr or exec_res.stdout or f"Probe binary failed execution (rc={exec_res.returncode})").strip()
                else:
                    last_err = (res.stderr or res.stdout or "Compiler probe failed to produce binary").strip()
            except Exception as e:
                last_err = str(e)

        if chosen_flags is not None:
            _C_COMPILER_INFO = {
                "available": True,
                "compiler": c_compiler,
                "flags": chosen_flags,
                "error": None
            }
        else:
            _C_COMPILER_INFO = {
                "available": False,
                "compiler": c_compiler,
                "flags": [],
                "error": f"C compiler probe failed: {last_err}"
            }
    except Exception as e:
        _C_COMPILER_INFO = {
            "available": False,
            "compiler": c_compiler,
            "flags": [],
            "error": f"C compiler probe error: {str(e)}"
        }
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)

    return _C_COMPILER_INFO


_CPP_COMPILER_INFO = None

def get_cpp_compiler_info():
    """
    Probes and caches C++ compiler availability and capabilities.
    Checks whether clang++ or g++ can compile and link a minimal C++ program with standard headers.
    Returns dict: {'available': bool, 'compiler': str, 'flags': list, 'error': str}
    """
    global _CPP_COMPILER_INFO
    if _CPP_COMPILER_INFO is not None:
        return _CPP_COMPILER_INFO

    cpp_compiler = shutil.which("clang++") or shutil.which("g++")
    if not cpp_compiler:
        _CPP_COMPILER_INFO = {
            "available": False,
            "compiler": None,
            "flags": [],
            "error": "C++ compiler (clang++/g++) not found in PATH."
        }
        return _CPP_COMPILER_INFO

    probe_dir = tempfile.mkdtemp(prefix="cpp_probe_")
    try:
        probe_src = os.path.join(probe_dir, "probe.cpp")
        probe_bin = os.path.join(probe_dir, "probe.bin")
        with open(probe_src, "w", encoding="utf-8") as f:
            f.write("#include <iostream>\n#include <cstddef>\nint main() { std::cout << \"ok\"; return 0; }\n")

        flag_candidates = [
            ["-std=c++17", "-O2", "-Wall"],
            ["-std=c++17", "-O2", "-Wall", "-lc++_shared"],
            ["-O2", "-Wall"],
            ["-O2", "-Wall", "-lc++_shared"],
        ]
        chosen_flags = None
        last_err = ""
        for flags in flag_candidates:
            try:
                cmd = [cpp_compiler] + flags + ["-o", probe_bin, probe_src]
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    errors="replace",
                    timeout=5
                )
                if res.returncode == 0 and os.path.exists(probe_bin):
                    exec_res = subprocess.run(
                        [probe_bin],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        errors="replace",
                        timeout=3
                    )
                    if exec_res.returncode == 0 and "ok" in exec_res.stdout:
                        chosen_flags = flags
                        break
                    else:
                        last_err = (exec_res.stderr or exec_res.stdout or f"Probe binary failed execution (rc={exec_res.returncode})").strip()
                else:
                    last_err = (res.stderr or res.stdout or "Compiler probe failed to produce binary").strip()
            except Exception as e:
                last_err = str(e)

        if chosen_flags is not None:
            _CPP_COMPILER_INFO = {
                "available": True,
                "compiler": cpp_compiler,
                "flags": chosen_flags,
                "error": None
            }
        else:
            _CPP_COMPILER_INFO = {
                "available": False,
                "compiler": cpp_compiler,
                "flags": [],
                "error": f"C++ compiler toolchain probe failed: {last_err}"
            }
    except Exception as e:
        _CPP_COMPILER_INFO = {
            "available": False,
            "compiler": cpp_compiler,
            "flags": [],
            "error": f"C++ compiler probe execution error: {str(e)}"
        }
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)

    return _CPP_COMPILER_INFO


def run_c_program(source_files, test_harness, timeout=5):
    """
    Compiles and executes C source files using clang/gcc.
    Runs in an isolated temporary directory.
    """
    compiler_info = get_c_compiler_info()
    if not compiler_info["available"]:
        return {
            "verdict": "COMPILER_UNAVAILABLE",
            "message": compiler_info.get("error") or "C compiler (clang/gcc) is not functional or not installed in this environment.",
            "console": f"C compiler unavailable: {compiler_info.get('error', 'compiler not found')}",
            "test_results": [],
            "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
        }

    c_compiler = compiler_info["compiler"]
    base_flags = compiler_info.get("flags") or ["-O2", "-Wall"]

    temp_dir = tempfile.mkdtemp(prefix="hdl_c_run_")
    try:
        # Write user source files (enforce C language isolation)
        c_src_paths = []
        c_header_paths = []
        for fname, content in source_files.items():
            if not isinstance(fname, str) or not any(fname.endswith(ext) for ext in ('.c', '.h')):
                continue
            fpath = os.path.join(temp_dir, os.path.basename(fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            if fname.endswith(".c"):
                c_src_paths.append(fpath)
            elif fname.endswith(".h"):
                c_header_paths.append(fpath)

        if not c_src_paths and not c_header_paths:
            return {
                "verdict": "COMPILE_ERROR",
                "message": "No C source files (.c, .h) found in submission.",
                "console": "Compilation error: Submission contains no valid C source files for C challenge.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }

        # Write test harness if present
        if isinstance(test_harness, dict) and "driver" in test_harness:
            driver_path = os.path.join(temp_dir, "driver.c")
            with open(driver_path, "w", encoding="utf-8") as f:
                f.write(test_harness["driver"])
            c_src_paths.append(driver_path)

        # If no .c files exist but headers exist, build a dummy driver
        if not c_src_paths and c_header_paths:
            dummy_driver = os.path.join(temp_dir, "_header_check.c")
            with open(dummy_driver, "w", encoding="utf-8") as f:
                for h in c_header_paths:
                    f.write(f'#include "{os.path.basename(h)}"\n')
                f.write("int main(void) { return 0; }\n")
            c_src_paths.append(dummy_driver)

        bin_path = os.path.join(temp_dir, "prog.bin")
        clang_cmd = [c_compiler] + base_flags + ["-I", temp_dir, "-o", bin_path] + c_src_paths

        # Compile
        compile_start = time.time()
        try:
            comp_res = subprocess.run(
                clang_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=timeout
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            return {
                "verdict": "COMPILER_UNAVAILABLE",
                "message": f"C compiler cannot be executed: {str(e)}",
                "console": f"C compiler execution error: {str(e)}",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }
        except subprocess.TimeoutExpired:
            return {
                "verdict": "COMPILE_ERROR",
                "message": "Compilation timed out.",
                "console": "C compilation exceeded timeout limit.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
            }

        if comp_res.returncode != 0:
            stderr_out = comp_res.stderr or comp_res.stdout or ""
            if is_toolchain_error(stderr_out) or comp_res.returncode in (126, 127):
                return {
                    "verdict": "COMPILER_UNAVAILABLE",
                    "message": "C compiler toolchain is unavailable or missing required system libraries in this environment.",
                    "console": stderr_out,
                    "test_results": [],
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
                }
            return {
                "verdict": "COMPILE_ERROR",
                "message": "C Compilation failed with errors.",
                "console": stderr_out,
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
            }

        # Execute
        run_start = time.time()
        try:
            exec_res = subprocess.run(
                [bin_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=timeout
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            return {
                "verdict": "RUNTIME_ERROR",
                "message": f"Failed to execute compiled C binary: {str(e)}",
                "console": str(e),
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }
        except subprocess.TimeoutExpired:
            return {
                "verdict": "TIME_LIMIT_EXCEEDED",
                "message": f"Execution exceeded maximum execution time of {timeout}s.",
                "console": "Time Limit Exceeded.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": timeout * 1000}
            }

        exec_time_ms = int((time.time() - run_start) * 1000)
        stdout = exec_res.stdout
        stderr = exec_res.stderr

        # Parse test results from stdout format ::TEST::id::name::status::detail::time::hidden
        test_results = []
        passed_count = 0
        total_count = 0
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("::TEST::"):
                parts = line.split("::")
                if len(parts) >= 5:
                    t_id = parts[2]
                    t_name = parts[3]
                    status = parts[4].upper()
                    detail = parts[5] if len(parts) > 5 else ""
                    is_hidden = bool(int(parts[7])) if len(parts) >= 8 and parts[7].isdigit() else False
                    passed = (status == "PASSED")
                    total_count += 1
                    if passed:
                        passed_count += 1
                    test_results.append({
                        "id": t_id,
                        "name": t_name,
                        "passed": passed,
                        "detail": detail,
                        "is_hidden": is_hidden
                    })

        if total_count == 0:
            if exec_res.returncode == 0:
                verdict = "ACCEPTED"
                passed_count = 1
                total_count = 1
                test_results.append({
                    "id": "tc_01",
                    "name": "Program Execution",
                    "passed": True,
                    "detail": "Program exited with code 0",
                    "is_hidden": False
                })
            else:
                verdict = "RUNTIME_ERROR"
        else:
            verdict = "ACCEPTED" if passed_count == total_count else "WRONG_ANSWER"

        return {
            "verdict": verdict,
            "message": f"{passed_count}/{total_count} tests passed." if total_count > 0 else "Execution complete.",
            "console": stdout + ("\n" + stderr if stderr else ""),
            "test_results": test_results,
            "stats": {"passed": passed_count, "total": total_count, "exec_time_ms": exec_time_ms}
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_cpp_program(source_files, test_harness, timeout=6):
    """
    Compiles and executes C++ source files using clang++/g++.
    Runs in an isolated temporary directory.
    """
    compiler_info = get_cpp_compiler_info()
    if not compiler_info["available"]:
        return {
            "verdict": "COMPILER_UNAVAILABLE",
            "message": compiler_info.get("error") or "C++ compiler (clang++/g++) is not functional or not installed in this environment.",
            "console": f"C++ compiler unavailable: {compiler_info.get('error', 'compiler not found')}",
            "test_results": [],
            "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
        }

    cpp_compiler = compiler_info["compiler"]
    base_flags = compiler_info.get("flags") or ["-std=c++17", "-O2", "-Wall"]

    temp_dir = tempfile.mkdtemp(prefix="hdl_cpp_run_")
    try:
        # Write user source files (enforce C++ language isolation)
        cpp_src_paths = []
        cpp_header_paths = []
        for fname, content in source_files.items():
            if not isinstance(fname, str) or not any(fname.endswith(ext) for ext in ('.cpp', '.cc', '.cxx', '.hpp', '.h')):
                continue
            fpath = os.path.join(temp_dir, os.path.basename(fname))
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            if fname.endswith((".cpp", ".cc", ".cxx")):
                cpp_src_paths.append(fpath)
            elif fname.endswith((".hpp", ".h")):
                cpp_header_paths.append(fpath)

        if not cpp_src_paths and not cpp_header_paths:
            return {
                "verdict": "COMPILE_ERROR",
                "message": "No C++ source files (.cpp, .cc, .hpp, .h) found in submission.",
                "console": "Compilation error: Submission contains no valid C++ source files for C++ challenge.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }

        if isinstance(test_harness, dict) and "driver" in test_harness:
            driver_path = os.path.join(temp_dir, "driver.cpp")
            with open(driver_path, "w", encoding="utf-8") as f:
                f.write(test_harness["driver"])
            cpp_src_paths.append(driver_path)

        # If no .cpp/.cc source exists but headers exist, build a dummy test driver
        if not cpp_src_paths and cpp_header_paths:
            dummy_driver = os.path.join(temp_dir, "_header_check.cpp")
            with open(dummy_driver, "w", encoding="utf-8") as f:
                for h in cpp_header_paths:
                    f.write(f'#include "{os.path.basename(h)}"\n')
                f.write("int main() { return 0; }\n")
            cpp_src_paths.append(dummy_driver)

        bin_path = os.path.join(temp_dir, "prog_cpp.bin")
        clangpp_cmd = [cpp_compiler] + base_flags + ["-I", temp_dir, "-o", bin_path] + cpp_src_paths

        compile_start = time.time()
        try:
            comp_res = subprocess.run(
                clangpp_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=timeout
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            return {
                "verdict": "COMPILER_UNAVAILABLE",
                "message": f"C++ compiler cannot be executed: {str(e)}",
                "console": f"C++ compiler execution error: {str(e)}",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }
        except subprocess.TimeoutExpired:
            return {
                "verdict": "COMPILE_ERROR",
                "message": "C++ compilation timed out.",
                "console": "C++ compilation exceeded timeout limit.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
            }

        if comp_res.returncode != 0:
            stderr_out = comp_res.stderr or comp_res.stdout or ""
            if is_toolchain_error(stderr_out) or comp_res.returncode in (126, 127):
                return {
                    "verdict": "COMPILER_UNAVAILABLE",
                    "message": "C++ compiler toolchain is unavailable or missing required standard libraries in this environment.",
                    "console": stderr_out,
                    "test_results": [],
                    "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
                }
            return {
                "verdict": "COMPILE_ERROR",
                "message": "C++ Compilation failed with errors.",
                "console": stderr_out,
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": int((time.time() - compile_start) * 1000)}
            }

        run_start = time.time()
        try:
            exec_res = subprocess.run(
                [bin_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                timeout=timeout
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            return {
                "verdict": "RUNTIME_ERROR",
                "message": f"Failed to execute compiled C++ binary: {str(e)}",
                "console": str(e),
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }
        except subprocess.TimeoutExpired:
            return {
                "verdict": "TIME_LIMIT_EXCEEDED",
                "message": f"Execution timed out after {timeout}s.",
                "console": "Time Limit Exceeded.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": timeout * 1000}
            }

        exec_time_ms = int((time.time() - run_start) * 1000)
        stdout = exec_res.stdout
        stderr = exec_res.stderr

        test_results = []
        passed_count = 0
        total_count = 0
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("::TEST::"):
                parts = line.split("::")
                if len(parts) >= 5:
                    t_id = parts[2]
                    t_name = parts[3]
                    status = parts[4].upper()
                    detail = parts[5] if len(parts) > 5 else ""
                    is_hidden = bool(int(parts[7])) if len(parts) >= 8 and parts[7].isdigit() else False
                    passed = (status == "PASSED")
                    total_count += 1
                    if passed:
                        passed_count += 1
                    test_results.append({
                        "id": t_id,
                        "name": t_name,
                        "passed": passed,
                        "detail": detail,
                        "is_hidden": is_hidden
                    })

        if total_count == 0:
            if exec_res.returncode == 0:
                verdict = "ACCEPTED"
                passed_count = 1
                total_count = 1
                test_results.append({
                    "id": "tc_01",
                    "name": "C++ Execution",
                    "passed": True,
                    "detail": "Program exited cleanly",
                    "is_hidden": False
                })
            else:
                verdict = "RUNTIME_ERROR"
        else:
            verdict = "ACCEPTED" if passed_count == total_count else "WRONG_ANSWER"

        return {
            "verdict": verdict,
            "message": f"{passed_count}/{total_count} tests passed." if total_count > 0 else "Execution complete.",
            "console": stdout + ("\n" + stderr if stderr else ""),
            "test_results": test_results,
            "stats": {"passed": passed_count, "total": total_count, "exec_time_ms": exec_time_ms}
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_python_program(source_files, test_harness, timeout=4):
    """
    Executes Python source files against test_harness cases in isolated temp directory.
    """
    # Language isolation check: ensure Python source file exists
    user_py = source_files.get("solution.py")
    if not user_py:
        for fname, content in source_files.items():
            if isinstance(fname, str) and fname.endswith(".py"):
                user_py = content
                break

    if not user_py:
        return {
            "verdict": "RUNTIME_ERROR",
            "message": "No Python source files (.py) found in submission.",
            "console": "Execution error: Submission contains no valid Python source files for Python challenge.",
            "test_results": [],
            "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
        }

    temp_dir = tempfile.mkdtemp(prefix="hdl_py_run_")
    try:
        src_path = os.path.join(temp_dir, "solution.py")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(user_py)

        # Build test driver script
        test_cases = test_harness.get("test_cases", [])
        driver_script = f"""
import sys
import json
import solution

test_cases = {repr(test_cases)}
pass_count = 0

for i, tc in enumerate(test_cases):
    tc_input = tc.get("input")
    expected = tc.get("expected")
    hidden = tc.get("hidden", False)
    t_id = f"tc_{{i+1:02d}}"
    try:
        if isinstance(tc_input, dict):
            actual = solution.compute_parity(**tc_input)
        elif isinstance(tc_input, (list, tuple)):
            actual = solution.compute_parity(*tc_input)
        else:
            actual = solution.compute_parity(tc_input)

        matched = (actual == expected)
        if matched:
            pass_count += 1
            print(f"::TEST::{{t_id}}::Input {{tc_input}}::PASSED::Actual={{actual}}::0ns::{{1 if hidden else 0}}")
        else:
            print(f"::TEST::{{t_id}}::Input {{tc_input}}::FAILED::Expected={{expected}}, Actual={{actual}}::0ns::{{1 if hidden else 0}}")
    except Exception as e:
        print(f"::TEST::{{t_id}}::Input {{tc_input}}::FAILED::Exception: {{e}}::0ns::{{1 if hidden else 0}}")

print(f"::TOTAL::{{pass_count}}::{{len(test_cases)}}")
"""
        driver_path = os.path.join(temp_dir, "driver.py")
        with open(driver_path, "w", encoding="utf-8") as f:
            f.write(driver_script)

        start_t = time.time()
        try:
            res = subprocess.run(
                [sys.executable, driver_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=temp_dir,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {
                "verdict": "TIME_LIMIT_EXCEEDED",
                "message": f"Execution timed out after {timeout} seconds.",
                "console": "Time Limit Exceeded.",
                "test_results": [],
                "stats": {"passed": 0, "total": len(test_cases), "exec_time_ms": timeout * 1000}
            }

        exec_time_ms = int((time.time() - start_t) * 1000)
        stdout = res.stdout
        stderr = res.stderr

        if res.returncode != 0 and not stdout:
            return {
                "verdict": "RUNTIME_ERROR",
                "message": "Python execution threw an unhandled exception.",
                "console": stderr,
                "test_results": [],
                "stats": {"passed": 0, "total": len(test_cases), "exec_time_ms": exec_time_ms}
            }

        test_results = []
        passed_count = 0
        total_count = 0
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("::TEST::"):
                parts = line.split("::")
                if len(parts) >= 8:
                    t_id = parts[2]
                    t_name = parts[3]
                    status = parts[4].upper()
                    detail = parts[5]
                    is_hidden = bool(int(parts[7])) if parts[7].isdigit() else False
                    passed = (status == "PASSED")
                    total_count += 1
                    if passed:
                        passed_count += 1
                    test_results.append({
                        "id": t_id,
                        "name": t_name,
                        "passed": passed,
                        "detail": detail,
                        "is_hidden": is_hidden
                    })

        verdict = "ACCEPTED" if (passed_count == total_count and total_count > 0) else "WRONG_ANSWER"
        return {
            "verdict": verdict,
            "message": f"{passed_count}/{total_count} tests passed.",
            "console": stdout + ("\n" + stderr if stderr else ""),
            "test_results": test_results,
            "stats": {"passed": passed_count, "total": total_count, "exec_time_ms": exec_time_ms}
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def extract_single_choice(raw_value) -> str:
    """Extracts normalized single-letter option key (A, B, C, D) from various input formats."""
    if not isinstance(raw_value, str):
        raw_value = str(raw_value) if raw_value is not None else ""
    cleaned = raw_value.strip()
    if not cleaned:
        return ""
    # Format: "Option A" or "Option: A"
    if cleaned.lower().startswith("option"):
        remainder = cleaned[6:].strip()
        if remainder and remainder[0] in (":", "-", " ", "."):
            remainder = remainder[1:].strip()
        if remainder:
            cleaned = remainder
    # Format: "A. Setup violations..." or "A) text" or "A: text"
    if len(cleaned) >= 2 and cleaned[0].isalpha() and cleaned[1] in (".", ")", ":", "-", " "):
        return cleaned[0].upper()
    # Format: "A"
    if len(cleaned) == 1 and cleaned.isalpha():
        return cleaned.upper()
    return cleaned.upper()


def evaluate_single_choice(question, answer_payload):
    """
    Evaluates a single-choice question with instant feedback, appreciation,
    and misconception explanation.
    """
    if not isinstance(answer_payload, dict):
        answer_payload = {}

    raw_choice = (
        answer_payload.get("choice") or
        answer_payload.get("selected") or
        answer_payload.get("option") or
        answer_payload.get("answer") or
        ""
    )
    choice = extract_single_choice(raw_choice)
    correct = question.get("correct_option", "").strip().upper()
    explanations = question.get("option_explanations", {})

    if not choice:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": "Please select an answer choice before submitting.",
            "feedback": "No option was selected.",
            "misconception_explanation": "Review the question statement carefully.",
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 1}
        }

    is_correct = (choice == correct)
    explanation = explanations.get(choice, question.get("explanation", ""))

    if is_correct:
        return {
            "verdict": "ACCEPTED",
            "score": 100,
            "message": f"Correct! Option {choice} is accurate.",
            "appreciation": "Excellent work! You accurately identified the core architectural principle.",
            "feedback": explanation,
            "explanation": explanation,
            "next_challenge_recommendation": "Try the next Intermediate question or explore Predict Output!",
            "stats": {"passed": 1, "total": 1, "exec_time_ms": 5}
        }
    else:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": f"Option {choice} is incorrect.",
            "feedback": "That choice is not accurate.",
            "misconception_explanation": explanation or "Review the fundamental timing equations and retry.",
            "next_challenge_recommendation": "Review the hint or try again!",
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 5}
        }


def evaluate_multiple_choice(question, answer_payload):
    """
    Evaluates a multiple-choice question.
    """
    raw_choices = answer_payload.get("choices") or []
    if isinstance(raw_choices, str):
        choices = set([c.strip().upper() for c in raw_choices.split(",") if c.strip()])
    else:
        choices = set([str(c).strip().upper() for c in raw_choices if str(c).strip()])

    correct = set([c.strip().upper() for c in question.get("correct_options", [])])

    if not choices:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": "Please select at least one option before submitting.",
            "feedback": "No options selected.",
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 2}
        }

    is_correct = (choices == correct)
    if is_correct:
        return {
            "verdict": "ACCEPTED",
            "score": 100,
            "message": f"Correct! All valid options ({', '.join(sorted(correct))}) selected.",
            "appreciation": "Brilliant! You mastered Verilog assignment semantics and IEEE coding guidelines.",
            "feedback": question.get("explanation", ""),
            "stats": {"passed": 1, "total": 1, "exec_time_ms": 5}
        }
    else:
        missing = correct - choices
        spurious = choices - correct
        detail_msg = []
        if missing:
            detail_msg.append(f"Missing correct option(s): {', '.join(sorted(missing))}")
        if spurious:
            detail_msg.append(f"Incorrect option(s) selected: {', '.join(sorted(spurious))}")

        return {
            "verdict": "WRONG_ANSWER",
            "score": max(0, int((len(choices & correct) / max(1, len(correct))) * 100)),
            "message": "Selection incomplete or contains incorrect choices.",
            "feedback": "; ".join(detail_msg),
            "misconception_explanation": question.get("explanation", "Remember Cummings' golden rules on blocking vs non-blocking."),
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 5}
        }


def normalize_predicted_output(raw_output: str) -> str:
    """Normalizes predicted output while preserving bit vectors, numbers, and signal values."""
    if not isinstance(raw_output, str):
        raw_output = str(raw_output) if raw_output is not None else ""
    s = raw_output.strip().lower()
    # Normalize spacing around commas and equals signs (e.g., "a=5, b=20" vs "a=5,b=20")
    s = re.sub(r'\s*,\s*', ',', s)
    s = re.sub(r'\s*=\s*', '=', s)
    # Strip enclosing quotes
    s = s.strip("\"' ")
    return s


def evaluate_predict_output(question, answer_payload):
    """
    Evaluates a predict-the-output challenge with whitespace/radix tolerance.
    Handles formatting differences without compromising numeric accuracy.
    """
    if not isinstance(answer_payload, dict):
        answer_payload = {}

    user_raw = (
        answer_payload.get("answer") or
        answer_payload.get("output") or
        answer_payload.get("prediction") or
        ""
    )
    user_out = str(user_raw).strip()

    if not user_out:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": "Please enter a predicted output before submitting.",
            "feedback": "Empty answer received.",
            "misconception_explanation": "Enter your predicted simulation value.",
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 1}
        }

    expected = question.get("expected_output", "").strip()
    acceptable = [a.strip() for a in question.get("acceptable_outputs", [expected]) if a.strip()]

    norm_user = normalize_predicted_output(user_out)
    norm_acceptable = [normalize_predicted_output(a) for a in acceptable]

    # Also check without internal underscores (e.g., 8'b1111_1100 vs 8'b11111100)
    norm_user_no_us = norm_user.replace("_", "")
    norm_acc_no_us = [a.replace("_", "") for a in norm_acceptable]

    is_correct = (norm_user in norm_acceptable) or (norm_user_no_us in norm_acc_no_us)

    if is_correct:
        return {
            "verdict": "ACCEPTED",
            "score": 100,
            "message": f"Spot on! Expected output matches: {user_out}",
            "appreciation": "Great eye! You accurately simulated the Verilog execution semantics.",
            "feedback": question.get("explanation", ""),
            "stats": {"passed": 1, "total": 1, "exec_time_ms": 4}
        }
    else:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": f"Predicted output '{user_out}' did not match simulation output.",
            "misconception_explanation": question.get("explanation", "Consider sign bit expansion or NBA scheduling order."),
            "stats": {"passed": 0, "total": 1, "exec_time_ms": 4}
        }


def evaluate_rubric(question, answer_payload):
    """
    Evaluates conceptual and interview scenarios using structured multi-point rubrics.
    Evaluates keyword presence, technical criteria coverage, and gives structured feedback.
    """
    user_text = (answer_payload.get("answer") or answer_payload.get("text") or "").strip()
    if not user_text:
        return {
            "verdict": "WRONG_ANSWER",
            "score": 0,
            "message": "Answer cannot be empty.",
            "feedback": "Please type your technical reasoning or architectural proposal.",
            "stats": {"passed": 0, "total": len(question.get("rubric_criteria", [])), "exec_time_ms": 1}
        }

    criteria = question.get("rubric_criteria", [])
    total_points = sum(c.get("points", 25) for c in criteria)
    earned_points = 0
    criterion_results = []
    text_lower = user_text.lower()

    for c in criteria:
        c_title = c.get("criterion", "Criterion")
        pts = c.get("points", 25)
        keywords = [k.lower() for k in c.get("keywords", [])]
        match_count = sum(1 for kw in keywords if kw in text_lower)
        # Needs at least 1-2 keywords or substantial explanation
        passed = (match_count >= max(1, min(2, len(keywords))))
        if passed:
            earned_points += pts
        criterion_results.append({
            "criterion": c_title,
            "passed": passed,
            "points": pts if passed else 0,
            "max_points": pts,
            "detail": f"Matched {match_count} key concept term(s)." if passed else "Missing key architectural considerations."
        })

    score_pct = int((earned_points / max(1, total_points)) * 100)
    verdict = "ACCEPTED" if score_pct >= 75 else "WRONG_ANSWER"

    return {
        "verdict": verdict,
        "score": score_pct,
        "message": f"Evaluation Score: {score_pct}% ({earned_points}/{total_points} pts).",
        "feedback": f"Your architectural explanation earned {score_pct}%.",
        "appreciation": "Exceptional technical depth! Your breakdown matches Staff/Principal level expectations." if score_pct >= 90 else None,
        "misconception_explanation": question.get("model_answer", ""),
        "rubric_results": criterion_results,
        "model_answer": question.get("model_answer", ""),
        "stats": {
            "passed": sum(1 for r in criterion_results if r["passed"]),
            "total": len(criterion_results),
            "exec_time_ms": 10
        }
    }


def execute_question(question, payload, test_mode="full"):
    """
    Main dispatching router for question evaluation.
    Inspects question type and language, executing with the appropriate pipeline.
    """
    q_type = question.get("type", "coding")
    q_lang = question.get("language", "verilog").lower()

    # 1. Non-coding questions
    if q_type == "single_choice":
        return evaluate_single_choice(question, payload)
    elif q_type == "multiple_choice":
        return evaluate_multiple_choice(question, payload)
    elif q_type == "predict_output":
        return evaluate_predict_output(question, payload)
    elif q_type in ("conceptual", "interview_scenario"):
        return evaluate_rubric(question, payload)

    # 2. Coding questions by language
    files = payload.get("files")
    code = payload.get("code")

    # If payload is directly a file dict (e.g. {"ring_buffer.hpp": "..."})
    if isinstance(payload, dict) and not files and not code:
        if any(isinstance(k, str) and k.endswith(('.v', '.sv', '.c', '.cpp', '.cc', '.h', '.hpp', '.py')) for k in payload.keys()):
            files = payload

    # If single code string provided, construct dictionary
    if not isinstance(files, dict) or not files:
        if isinstance(code, str) and code.strip():
            starter_files = question.get("starter_files", {})
            if starter_files:
                primary_fname = next(iter(starter_files.keys()))
                files = dict(starter_files)
                files[primary_fname] = code
            else:
                ext = "sv" if q_lang == "systemverilog" else ("c" if q_lang == "c" else ("cpp" if q_lang in ("cpp", "c++") else ("py" if q_lang == "python" else "v")))
                files = {f"{question.get('module_name', 'solution')}.{ext}": code}
        else:
            files = question.get("starter_files", {})

    if q_lang in ("verilog", "systemverilog"):
        return run_simulation(
            problem=question,
            files_input=files,
            language=q_lang,
            timeout=12,
            test_mode=test_mode
        )
    elif q_lang == "c":
        return run_c_program(files, question.get("test_harness", {}), timeout=6)
    elif q_lang in ("cpp", "c++"):
        return run_cpp_program(files, question.get("test_harness", {}), timeout=6)
    elif q_lang == "python":
        return run_python_program(files, question.get("test_harness", {}), timeout=5)
    else:
        # Default fallback to simulation
        return run_simulation(
            problem=question,
            files_input=files,
            language="verilog",
            timeout=12,
            test_mode=test_mode
        )
