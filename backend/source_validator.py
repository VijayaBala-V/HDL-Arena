"""
Verilog and SystemVerilog Source Validation Engine for HDL Arena.
Performs Stage 1 AST-level and lexical boundary checks on user submissions from 'module' to 'endmodule'.
Validates:
- Non-empty source.
- Module declarations vs expected top-module name.
- Balanced module ... endmodule boundaries.
- Support for multiple submodule declarations.
"""

import re


def strip_comments_and_strings(code: str) -> str:
    """
    Strips single-line (//) and multi-line (/* */) comments and string literals
    while preserving newlines so line numbers remain accurate.
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            # Count newlines to maintain line alignment
            return '\n' * s.count('\n')
        else:
            return '""'

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, code)


def validate_rtl_submission(files_dict: dict, expected_top_module: str):
    """
    Validates complete RTL submission files from 'module' to 'endmodule'.
    Returns (is_valid, error_payload_or_none, declared_modules_list).
    """
    if not files_dict or not isinstance(files_dict, dict):
        return False, {
            "verdict": "COMPILE_ERROR",
            "message": "Submission error: No source files were provided for compilation.",
            "diagnostics": {
                "file": "source.v",
                "line": 1,
                "evidence": ["Empty submission payload received by judge engine."],
                "recommendations": ["Ensure you have written your RTL code between 'module' and 'endmodule'."]
            }
        }, []

    all_declared_modules = []
    has_any_content = False

    for fname, raw_code in files_dict.items():
        if not isinstance(raw_code, str):
            continue

        trimmed = raw_code.strip()
        if trimmed:
            has_any_content = True

        stripped = strip_comments_and_strings(raw_code)

        # 1. Check for balanced module ... endmodule tokens
        # Find all occurrences of module / macromodule and endmodule
        module_matches = list(re.finditer(r'\b(?:module|macromodule)\s+([a-zA-Z_][a-zA-Z0-9_$]*)', stripped))
        endmodule_matches = list(re.finditer(r'\bendmodule\b', stripped))

        for m in module_matches:
            mod_name = m.group(1)
            all_declared_modules.append({
                "file": fname,
                "name": mod_name,
                "pos": m.start()
            })

        mod_count = len(module_matches)
        end_count = len(endmodule_matches)

        if mod_count > end_count:
            # Missing endmodule
            # Find the line number of the unclosed module
            last_mod = module_matches[-1]
            line_no = raw_code[:last_mod.start()].count('\n') + 1
            mod_name = last_mod.group(1)
            return False, {
                "verdict": "COMPILE_ERROR",
                "message": f"{fname}:{line_no}: Syntax error: Module '{mod_name}' is missing closing 'endmodule' directive.",
                "diagnostics": {
                    "file": fname,
                    "line": line_no,
                    "evidence": [f"Declared 'module {mod_name}' without a corresponding 'endmodule' keyword."],
                    "recommendations": ["Close the module with 'endmodule' at the end of your source code."]
                }
            }, []

        if end_count > mod_count:
            # Extraneous endmodule
            first_extra = endmodule_matches[mod_count]
            line_no = raw_code[:first_extra.start()].count('\n') + 1
            return False, {
                "verdict": "COMPILE_ERROR",
                "message": f"{fname}:{line_no}: Syntax error: Unexpected 'endmodule' directive without a preceding 'module' declaration.",
                "diagnostics": {
                    "file": fname,
                    "line": line_no,
                    "evidence": ["Encountered 'endmodule' without a matching 'module' declaration."],
                    "recommendations": ["Remove redundant 'endmodule' or ensure module declaration precedes it."]
                }
            }, []

    if not has_any_content:
        return False, {
            "verdict": "COMPILE_ERROR",
            "message": "Submission error: Source files are empty. Please implement the complete RTL module from 'module' to 'endmodule'.",
            "diagnostics": {
                "file": list(files_dict.keys())[0] if files_dict else "source.v",
                "line": 1,
                "evidence": ["All submitted files are empty or contain only whitespace."],
                "recommendations": ["Write your RTL module implementation in the editor before running."]
            }
        }, []

    # 2. Check for required top module
    declared_names = [m["name"] for m in all_declared_modules]

    if not declared_names:
        first_file = list(files_dict.keys())[0]
        return False, {
            "verdict": "COMPILE_ERROR",
            "message": f"Syntax error in {first_file}: No Verilog module declaration found. The submission must define 'module {expected_top_module} ... endmodule'.",
            "diagnostics": {
                "file": first_file,
                "line": 1,
                "evidence": ["No 'module <name>' header detected in submitted source."],
                "recommendations": [f"Start your implementation with 'module {expected_top_module}(' including its port list."]
            }
        }, []

    if expected_top_module and (expected_top_module not in declared_names):
        first_file = all_declared_modules[0]["file"]
        found_str = ", ".join(f"'{name}'" for name in declared_names)
        return False, {
            "verdict": "COMPILE_ERROR",
            "message": f"Top Module Name Mismatch: Expected top module '{expected_top_module}', but found {found_str}. Top module must match '{expected_top_module}'.",
            "diagnostics": {
                "file": first_file,
                "line": 1,
                "evidence": [f"Expected module name '{expected_top_module}' not found in declared modules: {found_str}."],
                "recommendations": [f"Rename your top module to 'module {expected_top_module}' so the testbench can instantiate it."]
            }
        }, declared_names

    return True, None, declared_names
