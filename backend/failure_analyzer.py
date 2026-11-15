import re

def analyze_failures(verdict, compiler_output, simulation_logs, test_results, cycle_logs, vcd_data):
    """
    RTL Diagnostic & Failure Analysis Service.
    Correlates simulation errors, cycle mismatches, VCD X/Z anomalies, and compiler warnings
    to generate evidence-backed engineering explanations and linked waveform timestamps.
    """
    diagnostics = {
        "status": verdict,
        "failed_scenarios": [],
        "evidence": [],
        "suspected_root_causes": [],
        "recommendations": [],
        "failure_time_ns": None,
        "failed_test_id": None,
        "first_mismatch": None
    }

    if verdict == "ACCEPTED":
        diagnostics["summary"] = "All assertions and timing checks passed verification without discrepancies."
        return diagnostics

    # 1. Compiler diagnostics & lint warnings
    if compiler_output:
        if "warning: implicit wire" in compiler_output.lower():
            diagnostics["evidence"].append("Implicit wire inferred by compiler. Check signal declaration spelling.")
            diagnostics["suspected_root_causes"].append("Typo in signal name or undeclared variable treated as 1-bit wire.")

        if "port" in compiler_output.lower() and "mismatch" in compiler_output.lower():
            diagnostics["evidence"].append("Module port size or connection count mismatch in instantiation.")
            diagnostics["suspected_root_causes"].append("Top module port list does not match problem interface specification.")

    # 2. Analyze failed test scenarios
    failed_tests = [t for t in test_results if t.get("status") == "FAILED"]
    for ft in failed_tests:
        diagnostics["failed_scenarios"].append({
            "id": ft.get("id"),
            "name": ft.get("name", "Unknown Test"),
            "detail": ft.get("detail", "Assertion failure"),
            "time_ns": ft.get("time_ns"),
            "is_hidden": ft.get("is_hidden", False)
        })

    if failed_tests:
        diagnostics["failed_test_id"] = failed_tests[0].get("id")
        if failed_tests[0].get("time_ns") is not None:
            diagnostics["failure_time_ns"] = failed_tests[0].get("time_ns")

    # 3. Analyze cycle-by-cycle mismatches
    mismatches = [c for c in cycle_logs if not c.get("match", True)]
    if mismatches:
        first_mismatch = mismatches[0]
        diagnostics["first_mismatch"] = first_mismatch
        t_fail = first_mismatch.get("time_num")
        if t_fail is not None:
            diagnostics["failure_time_ns"] = t_fail

        diagnostics["evidence"].append(
            f"Assertion mismatch detected at simulation timestamp {first_mismatch.get('time')}: "
            f"inputs={first_mismatch.get('inputs')} | expected={first_mismatch.get('expected')} | actual={first_mismatch.get('actual')}"
        )

        exp = str(first_mismatch.get("expected", ""))
        act = str(first_mismatch.get("actual", ""))

        # Check for 'x' unknown value in actual output
        if 'x' in act.lower():
            diagnostics["evidence"].append(f"Actual output contains unknown logic state 'X' ({act}) at failure time.")
            diagnostics["suspected_root_causes"].append(
                "Uninitialized register or unhandled reset condition. "
                "Ensure registers are assigned in a synchronous/asynchronous reset branch."
            )
            diagnostics["recommendations"].append(
                "Inspect the reset branch inside 'always @(posedge clk)'. Verify that all output registers have clear default reset values."
            )

        # Off-by-one counter analysis
        try:
            exp_int = int(exp, 16) if '0x' in exp else int(exp)
            act_int = int(act, 16) if '0x' in act else int(act)
            diff = act_int - exp_int
            if diff in (1, -1):
                diagnostics["evidence"].append(f"Output differs from expected value by exactly {diff} ({act_int} vs {exp_int}).")
                diagnostics["suspected_root_causes"].append(
                    "Off-by-one latency or counter update delay. "
                    "Ensure you are using non-blocking assignments (<=) and not double-incrementing registers."
                )
                diagnostics["recommendations"].append(
                    "Review whether output should reflect the current cycle's value or the registered value on the next clock edge."
                )
        except Exception:
            pass

    # 4. Check VCD anomalies (e.g. unknown states on buses)
    if vcd_data and vcd_data.get("x_anomalies"):
        anomalies = vcd_data["x_anomalies"][:4]
        for anom in anomalies:
            diagnostics["evidence"].append(
                f"Signal '{anom['signal']}' observed in undefined '{anom['value']}' state at {anom['time']}ns."
            )

    # 5. Domain-specific rule checks based on problem categories & logs
    lower_logs = simulation_logs.lower() if simulation_logs else ""

    if "reset" in lower_logs and ("fail" in lower_logs or "fatal" in lower_logs):
        diagnostics["suspected_root_causes"].append(
            "Incorrect reset polarity or synchronicity: Check if the reset is active-high ('if (rst)') or active-low ('if (!rst_n)')."
        )
        diagnostics["recommendations"].append(
            "Verify the problem specification for reset polarity and whether reset is synchronous or asynchronous."
        )

    if "fifo" in lower_logs and ("overflow" in lower_logs or "underflow" in lower_logs or "empty" in lower_logs):
        diagnostics["suspected_root_causes"].append(
            "FIFO pointer tracking error: Full and empty flags may not account for pointer wrap-around or dual-clock latency."
        )
        diagnostics["recommendations"].append(
            "Use an extra bit for write and read pointers (e.g., [ADDR_WIDTH:0]) to distinguish between full and empty states."
        )

    if "fsm" in lower_logs or "state" in lower_logs:
        diagnostics["suspected_root_causes"].append(
            "Missing state transition or latch inference: Ensure next_state has a default assignment at the beginning of the combinational block."
        )
        diagnostics["recommendations"].append(
            "Add 'next_state = state;' as the first statement in 'always @(*)' before the case statement."
        )

    # Fallback recommendations if none populated
    if not diagnostics["recommendations"]:
        diagnostics["recommendations"].append(
            "Inspect the waveform trace for input-to-output propagation delay."
        )
        diagnostics["recommendations"].append(
            "Ensure sequential logic uses non-blocking assignments '<=' and combinational logic uses '='."
        )

    # De-duplicate lists
    diagnostics["suspected_root_causes"] = list(dict.fromkeys(diagnostics["suspected_root_causes"]))
    diagnostics["recommendations"] = list(dict.fromkeys(diagnostics["recommendations"]))
    diagnostics["evidence"] = list(dict.fromkeys(diagnostics["evidence"]))

    return diagnostics
