import os
import sys
import time
from flask import Flask, jsonify, request, make_response, send_from_directory
from flask_cors import CORS
from questions_registry import QUESTIONS_REGISTRY, PROBLEMS_REGISTRY
from runner import execute_question
from compiler import run_simulation
import database

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

app = Flask(__name__)
CORS(app, supports_credentials=True)


def get_current_user(allow_fallback=True):
    """
    Retrieves the authenticated user from:
    1. Authorization header (Bearer token)
    2. X-Auth-Token header
    3. Cookie (hdl_auth_token or auth_token)
    4. Query string (?token=)
    5. Request JSON body (auth_token)
    
    If an explicit token is supplied but invalid or expired, returns None
    so endpoints can distinguish unauthorized sessions from unauthenticated guests.
    If no token is supplied and allow_fallback=True, returns the default account.
    """
    token = None
    token_supplied = False

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        token_supplied = True
    elif request.headers.get("X-Auth-Token"):
        token = request.headers.get("X-Auth-Token").strip()
        token_supplied = True
    elif request.cookies.get("hdl_auth_token"):
        token = request.cookies.get("hdl_auth_token").strip()
        token_supplied = True
    elif request.cookies.get("auth_token"):
        token = request.cookies.get("auth_token").strip()
        token_supplied = True
    elif request.args.get("token"):
        token = request.args.get("token").strip()
        token_supplied = True
    elif request.is_json:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict) and data.get("auth_token"):
            token = str(data["auth_token"]).strip()
            token_supplied = True

    if token:
        if token.lower() in ("undefined", "null", "", "none"):
            token = None
            token_supplied = False
        else:
            user = database.get_user_by_token(token)
            if user:
                return user
            # Token was provided but is invalid or expired
            return None

    if token_supplied:
        # A token header/key was provided but was empty/whitespace
        return None

    if allow_fallback:
        return database.get_or_create_default_user()

    return None


@app.get("/")
def home():
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(DIST_DIR, "index.html")
    return jsonify({
        "platform": "HDL Arena — Professional RTL Verification Platform",
        "version": "2.2.0",
        "engine": "Icarus Verilog (iverilog & vvp)",
        "message": "Frontend build not detected in frontend/dist. Start Vite dev server with 'npm run dev' or build with 'npm run build'."
    })


@app.get("/assets/<path:filename>")
def serve_assets(filename):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(os.path.join(assets_dir, filename)):
        return send_from_directory(assets_dir, filename)
    return jsonify({"error": "Asset not found"}), 404


@app.errorhandler(404)
def handle_404(e):
    if not request.path.startswith("/api/"):
        rel_path = request.path.lstrip("/")
        candidate = os.path.join(DIST_DIR, rel_path)
        if rel_path and os.path.isfile(candidate):
            return send_from_directory(DIST_DIR, rel_path)
        index_path = os.path.join(DIST_DIR, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(DIST_DIR, "index.html")
    return jsonify({
        "error": "Not Found",
        "message": f"Endpoint '{request.path}' was not found on this server.",
        "status": 404
    }), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({
        "error": "Method Not Allowed",
        "message": f"HTTP {request.method} is not supported for '{request.path}'.",
        "status": 405
    }), 405


@app.errorhandler(400)
def handle_400(e):
    return jsonify({
        "error": "Bad Request",
        "message": str(e),
        "status": 400
    }), 400


@app.after_request
def add_cors_and_security_headers(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Auth-Token"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options_preflight(path):
    resp = make_response("", 204)
    origin = request.headers.get("Origin", "*")
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Auth-Token"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resp


@app.errorhandler(Exception)
def handle_unexpected_exception(e):
    import traceback
    traceback.print_exc()
    error_msg = str(e) or "An unexpected server error occurred while processing the request."
    return jsonify({
        "ok": False,
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": error_msg
        },
        "message": error_msg,
        "status": 500
    }), 500


# =============================================================================
# AUTHENTICATION & ACCOUNT ENDPOINTS
# =============================================================================

@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = database.authenticate_or_register(username, password)
    if not user:
        return jsonify({"error": "Invalid credentials."}), 401

    resp = make_response(jsonify({
        "status": "authenticated",
        "user_id": user["id"],
        "username": user["username"],
        "token": user["auth_token"]
    }))
    # Set session cookie for seamless mobile/desktop cross-origin support
    resp.set_cookie(
        "hdl_auth_token",
        user["auth_token"],
        max_age=30 * 86400,
        httponly=False,
        samesite="Lax",
        path="/"
    )
    return resp


@app.get("/api/account/me")
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Session expired or invalid credentials."}), 401

    coins_info = database.get_user_coins_info(user["id"])
    return jsonify({
        "user_id": user["id"],
        "username": user["username"],
        "token": user["auth_token"],
        **coins_info
    })


@app.get("/api/account/coins")
@app.get("/api/coins")
@app.get("/api/user/coins")
def get_account_coins():
    user = get_current_user()
    if not user:
        return jsonify({
            "error": "Unauthorized: Unable to fetch VJ Coin balance without a valid session. Please log in.",
            "coins": None
        }), 401

    info = database.get_user_coins_info(user["id"])
    return jsonify({
        "status": "ok",
        "user_id": user["id"],
        "username": user["username"],
        **info
    })


@app.get("/api/account/streak")
def get_account_streak():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in."}), 401
    streak_info = database.get_user_streak_info(user["id"])
    return jsonify(streak_info)


@app.post("/api/account/daily-reward")
def claim_account_daily_reward():
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Unauthorized: Please log in to claim daily VJ Coins."
                },
                "status": 401,
                "message": "Unauthorized: Please log in to claim daily VJ Coins.",
                "awarded": False
            }), 401

        result = database.claim_daily_reward(user["id"])
        # Support both new standardized ok/data format and existing direct keys for zero regression
        return jsonify({
            "ok": True,
            "data": result,
            **result
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        err_msg = str(e) or "An error occurred while claiming your daily login reward."
        return jsonify({
            "ok": False,
            "error": {
                "code": "DAILY_REWARD_ERROR",
                "message": err_msg
            },
            "status": 500,
            "message": err_msg,
            "awarded": False,
            "already_claimed": False
        }), 500


@app.get("/api/account/transactions")
def get_account_transactions():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in."}), 401
    limit = int(request.args.get("limit", 30))
    txs = database.get_user_transactions(user["id"], limit=limit)
    return jsonify(txs)


# =============================================================================
# QUESTION & PROBLEM CATALOG & HINT/SOLUTION ACCESS ENDPOINTS
# =============================================================================

@app.get("/api/questions")
@app.get("/api/problems")
def list_questions():
    """
    Returns filtered questions list.
    Supports filtering by:
    - category / topic
    - difficulty (Beginner, Intermediate, Advanced, Expert)
    - language (verilog, systemverilog, c, cpp, python)
    - type (coding, single_choice, multiple_choice, predict_output, fill_in_code, debugging, conceptual, interview_scenario)
    - status (solved, unattempted, bookmarked, mistakes, attempted)
    - search
    """
    user = get_current_user()
    user_id = user["id"] if user else 1

    category = request.args.get("category") or request.args.get("topic")
    difficulty = request.args.get("difficulty")
    language = request.args.get("language")
    q_type = request.args.get("type")
    status = request.args.get("status", "all").lower()
    search = request.args.get("search", "").lower().strip()

    unlocked_list = database.get_unlocked_solutions_for_user(user_id)
    user_progress = database.get_user_interview_progress(user_id)
    solved_set = set(user_progress.get("solved_ids", []))
    attempted_set = set(user_progress.get("attempted_ids", []))
    mistake_set = set(user_progress.get("mistake_ids", []))
    bookmark_set = set(user_progress.get("bookmarks", []))

    results = []
    for p in QUESTIONS_REGISTRY.values():
        p_cat = p.get("topic") or p.get("category", "")
        p_diff = p.get("difficulty", "Beginner")
        p_lang = p.get("language", "verilog").lower()
        p_type = p.get("type", "coding").lower()
        p_id = p["id"]

        # Category/topic filter
        if category and category != "All" and p_cat != category and p.get("category") != category:
            continue

        # Difficulty filter (Case-insensitive)
        if difficulty and difficulty != "All":
            if p_diff.lower() != difficulty.lower():
                # Allow 'Easy' to match 'Beginner', 'Medium' to match 'Intermediate', 'Hard' to match 'Advanced'
                diff_map = {"easy": "beginner", "medium": "intermediate", "hard": "advanced"}
                norm_req = diff_map.get(difficulty.lower(), difficulty.lower())
                norm_p = diff_map.get(p_diff.lower(), p_diff.lower())
                if norm_req != norm_p:
                    continue

        # Language filter
        if language and language != "All":
            norm_lang = language.lower()
            if norm_lang == "c++":
                norm_lang = "cpp"
            p_norm_lang = "cpp" if p_lang in ("cpp", "c++") else p_lang
            if p_norm_lang != norm_lang:
                continue

        # Question Type filter
        if q_type and q_type != "All":
            if p_type != q_type.lower():
                continue

        # Status filter
        is_solved = p_id in solved_set
        is_bookmarked = p_id in bookmark_set
        is_mistake = p_id in mistake_set
        is_attempted = p_id in attempted_set

        if status == "solved" and not is_solved:
            continue
        elif status == "unattempted" and is_attempted:
            continue
        elif status == "unsolved" and is_solved:
            continue
        elif status == "bookmarked" and not is_bookmarked:
            continue
        elif (status in ("mistakes", "review_mistakes")) and not is_mistake:
            continue
        elif status == "attempted" and not is_attempted:
            continue

        # Text search
        if search:
            title_match = search in p.get("title", "").lower()
            id_match = search in p_id.lower()
            tags_match = any(search in t.lower() for t in p.get("tags", []))
            topic_match = search in p_cat.lower()
            if not (title_match or id_match or tags_match or topic_match):
                continue

        desc_snippet = (p.get("description") or "")[:150].replace("\n", " ") + "..."

        results.append({
            "id": p_id,
            "title": p.get("title", p_id),
            "topic": p_cat,
            "category": p_cat,
            "difficulty": p_diff,
            "language": p_lang,
            "type": p_type,
            "tags": p.get("tags", []),
            "description": desc_snippet,
            "module_name": p.get("module_name", p_id),
            "ports_count": len(p.get("ports", [])),
            "is_unlocked": (p_id in unlocked_list),
            "is_solved": is_solved,
            "is_bookmarked": is_bookmarked,
            "is_mistake": is_mistake
        })

    return jsonify(results)


@app.get("/api/questions/<question_id>")
@app.get("/api/problems/<question_id>")
def get_question(question_id):
    """
    Returns question metadata, interface/template, and progressive hints.
    Never exposes hidden test cases or canonical solution.
    """
    p = QUESTIONS_REGISTRY.get(question_id)
    if not p:
        return jsonify({"error": f"Question '{question_id}' not found"}), 404

    user = get_current_user()
    user_id = user["id"] if user else 1

    # Check saved draft for this user & question
    saved_draft = database.get_draft(user_id, question_id)
    if saved_draft and isinstance(saved_draft, dict):
        has_content = any(isinstance(v, str) and v.strip() for v in saved_draft.values())
        if not has_content:
            saved_draft = None
    else:
        saved_draft = None

    # Check solution unlock status
    is_solution_unlocked = database.is_solution_unlocked(user_id, question_id)

    # Check paid hint unlocks
    unlocked_hint_indices = set(database.get_unlocked_hints_for_problem(user_id, question_id))

    # Build progressive hints structure
    raw_progressive = p.get("progressive_hints")
    if not raw_progressive:
        base_hints = p.get("hints", [
            f"Review the declaration for '{p.get('module_name', question_id)}' and verify all ports.",
            "Ensure assignments inside clocked always blocks use non-blocking assignments (<=).",
            "Check boundary conditions and reset handling."
        ])
        raw_progressive = []
        for idx, h_text in enumerate(base_hints):
            raw_progressive.append({
                "index": idx,
                "cost": 0.0 if idx == 0 else 0.5,
                "title": f"Hint {idx + 1}" if idx > 0 else "Conceptual Nudge (Free)",
                "text": h_text
            })

    sanitized_hints = []
    for h in raw_progressive:
        h_idx = h.get("index", 0)
        h_cost = float(h.get("cost", 0.0))
        # Hint 0 is free; index >= 1 requires unlock
        is_unlocked = (h_cost == 0.0) or (h_idx in unlocked_hint_indices)

        hint_item = {
            "index": h_idx,
            "cost": h_cost,
            "title": h.get("title", f"Hint {h_idx + 1}"),
            "is_unlocked": is_unlocked
        }
        if is_unlocked:
            hint_item["text"] = h.get("text", "")
        else:
            hint_item["teaser"] = f"Unlock implementation clue for {h_cost} VJ Coin."

        sanitized_hints.append(hint_item)

    # Legacy flat hints list for existing components (includes unlocked hints + placeholders)
    legacy_hints = []
    for h in sanitized_hints:
        if h["is_unlocked"]:
            legacy_hints.append(h["text"])
        else:
            legacy_hints.append(f"🔒 Locked Hint ({h['cost']} VJ Coin)")

    response_payload = {
        "id": p["id"],
        "title": p.get("title", question_id),
        "topic": p.get("topic") or p.get("category", "Digital Logic"),
        "category": p.get("category") or p.get("topic", "Digital Logic"),
        "difficulty": p.get("difficulty", "Beginner"),
        "language": p.get("language", "verilog"),
        "type": p.get("type", "coding"),
        "tags": p.get("tags", []),
        "description": p.get("description", ""),
        "requirements": p.get("requirements", []),
        "constraints": p.get("constraints", []),
        "module_name": p.get("module_name", question_id),
        "ports": p.get("ports", []),
        "interface": p.get("interface", ""),
        "starter_files": p.get("starter_files", {}),
        "options": p.get("options", []),
        "rubric_criteria": p.get("rubric_criteria", []),
        "source_metadata": p.get("source_metadata", {}),
        "test_suite_version": p.get("test_suite_version", "1.0.0"),
        "saved_draft": saved_draft,
        "is_unlocked": is_solution_unlocked,
        "solution_cost": 1.0,  # 1.0 VJ Coin
        "progressive_hints": sanitized_hints,
        "hints": legacy_hints
    }

    return jsonify(response_payload)


@app.post("/api/questions/<question_id>/hints/<int:hint_idx>/unlock")
@app.post("/api/problems/<question_id>/hints/<int:hint_idx>/unlock")
def unlock_hint_endpoint(question_id, hint_idx):
    """
    Unlocks a paid hint (0.5 VJ Coin) for a specific question using atomic database deduction.
    """
    p = QUESTIONS_REGISTRY.get(question_id)
    if not p:
        return jsonify({"ok": False, "error": f"Question '{question_id}' not found"}), 404

    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Unauthorized: Please log in to unlock hints."}), 401

    # Verify hint exists in question
    prog_hints = p.get("progressive_hints", [])
    target_hint = None
    for h in prog_hints:
        if h.get("index") == hint_idx:
            target_hint = h
            break

    if not target_hint:
        # Fallback to general hints
        base_hints = p.get("hints", [])
        if 0 <= hint_idx < len(base_hints):
            target_hint = {
                "index": hint_idx,
                "cost": 0.0 if hint_idx == 0 else 0.5,
                "title": f"Hint {hint_idx + 1}",
                "text": base_hints[hint_idx]
            }

    if not target_hint:
        return jsonify({"ok": False, "error": f"Hint index {hint_idx} not found for '{question_id}'"}), 404

    # Free hint 0
    if float(target_hint.get("cost", 0.0)) == 0.0:
        return jsonify({
            "ok": True,
            "success": True,
            "hint_index": hint_idx,
            "hint_text": target_hint.get("text"),
            "coins": database.get_user_coins_info(user["id"]).get("coins", 0.0)
        })

    # Paid hint: unlock with atomic transaction in DB
    result = database.unlock_paid_hint(user["id"], question_id, hint_idx)
    if result.get("success"):
        result["ok"] = True
        result["hint_text"] = target_hint.get("text")
        result["hint_title"] = target_hint.get("title")
        return jsonify(result), 200
    else:
        result["ok"] = False
        return jsonify(result), 400


@app.get("/api/questions/<question_id>/hints")
@app.get("/api/problems/<question_id>/hints")
def get_hints_list(question_id):
    p = QUESTIONS_REGISTRY.get(question_id)
    if not p:
        return jsonify({"error": f"Question '{question_id}' not found", "hints": []}), 404

    user = get_current_user()
    user_id = user["id"] if user else 1
    unlocked_indices = set(database.get_unlocked_hints_for_problem(user_id, question_id))

    prog_hints = p.get("progressive_hints", [])
    if not prog_hints:
        base = p.get("hints", [])
        prog_hints = [
            {"index": i, "cost": 0.0 if i == 0 else 0.5, "title": f"Hint {i+1}", "text": t}
            for i, t in enumerate(base)
        ]

    sanitized = []
    for h in prog_hints:
        h_idx = h.get("index", 0)
        h_cost = float(h.get("cost", 0.0))
        is_unlocked = (h_cost == 0.0) or (h_idx in unlocked_indices)
        item = {
            "index": h_idx,
            "cost": h_cost,
            "title": h.get("title", f"Hint {h_idx+1}"),
            "is_unlocked": is_unlocked
        }
        if is_unlocked:
            item["text"] = h.get("text", "")
        sanitized.append(item)

    return jsonify({"question_id": question_id, "hints": sanitized})


@app.post("/api/questions/<question_id>/unlock-solution")
@app.post("/api/problems/<question_id>/unlock-solution")
def unlock_solution_route(question_id):
    """
    Unlocks reference solution for 1 VJ Coin using an atomic transaction.
    Returns reference solution only upon successful deduction or prior unlock.
    """
    p = QUESTIONS_REGISTRY.get(question_id)
    if not p:
        return jsonify({"success": False, "error": f"Question '{question_id}' not found"}), 404

    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Unauthorized: Please log in to unlock solutions."}), 401

    result = database.unlock_solution(user["id"], question_id)
    if result.get("success"):
        result["solution"] = p.get("solution")
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.get("/api/questions/<question_id>/solution")
@app.get("/api/problems/<question_id>/solution")
def get_unlocked_solution(question_id):
    """
    Returns reference solution ONLY IF the user has already unlocked it.
    Otherwise returns 403 Forbidden.
    """
    p = QUESTIONS_REGISTRY.get(question_id)
    if not p:
        return jsonify({"error": f"Question '{question_id}' not found"}), 404

    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in to view unlocked solution."}), 401

    if not database.is_solution_unlocked(user["id"], question_id):
        return jsonify({
            "error": "Reference solution is locked. Unlock it for 1 VJ Coin."
        }), 403

    return jsonify({
        "question_id": question_id,
        "is_unlocked": True,
        "solution": p.get("solution")
    })


# =============================================================================
# UNIFIED SUBMISSION & EXECUTION PIPELINE
# =============================================================================

@app.post("/api/questions/<question_id>/submit")
@app.post("/api/submit")
def submit(question_id=None):
    """
    Unified submission handler for all question types and languages.
    Executes in sandboxed runner, records attempts, updates mistakes list,
    and awards authoritative VJ Coins on first solve.
    """
    try:
        data = request.get_json(silent=True) or {}
        q_id = question_id or data.get("problem_id") or data.get("question_id") or "counter4"
        test_mode = data.get("mode", request.args.get("mode", "full")).lower()

        if q_id not in QUESTIONS_REGISTRY:
            return jsonify({
                "ok": False,
                "error": {
                    "code": "QUESTION_NOT_FOUND",
                    "message": f"Question '{q_id}' not found in registry."
                },
                "verdict": "INTERNAL_JUDGE_ERROR",
                "message": f"Question '{q_id}' not found in registry.",
                "console": f"Question '{q_id}' not found in registry.",
                "test_results": [],
                "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
            }), 404

        question = QUESTIONS_REGISTRY[q_id]
        user = get_current_user()
        user_id = user["id"] if user else 1

        # Execute using runner
        exec_start = time.time()
        result = execute_question(question, data, test_mode=test_mode)
        exec_time = int((time.time() - exec_start) * 1000)

        # Ensure consistent structure
        result["ok"] = True
        verdict = result.get("verdict", "RUNTIME_ERROR")
        stats = result.get("stats", {})
        if "exec_time_ms" not in stats:
            stats["exec_time_ms"] = exec_time

        result["data"] = {
            "verdict": verdict,
            "message": result.get("message", ""),
            "stats": stats
        }

        # Record attempt & manage mistakes list in database
        try:
            score = result.get("score", 100 if verdict == "ACCEPTED" else 0)
            feedback = result.get("feedback") or result.get("misconception_explanation") or result.get("message", "")
            database.record_question_attempt(
                user_id=user_id,
                question_id=q_id,
                question_type=question.get("type", "coding"),
                verdict=verdict,
                answer_payload=data,
                score=score,
                feedback=feedback
            )
        except Exception as e:
            print(f"[HDL Arena] Warning: record_question_attempt error: {e}")

        # Record legacy submission if coding
        if test_mode == "full":
            try:
                database.record_submission(
                    user_id=user_id,
                    problem_id=q_id,
                    verdict=verdict,
                    message=result.get("message", ""),
                    tests_passed=stats.get("passed", 0),
                    tests_total=stats.get("total", 0),
                    exec_time_ms=stats.get("exec_time_ms", 0),
                    language=question.get("language", "verilog"),
                    code_snapshot=data.get("files") or data.get("code") or data
                )
            except Exception as e:
                print(f"[HDL Arena] Warning: record_submission error: {e}")

            # Award 1 VJ coin for Medium, Hard, Advanced, or Expert first solve
            if verdict == "ACCEPTED":
                try:
                    difficulty = question.get("difficulty", "Beginner")
                    reward_info = database.award_problem_completion(
                        user_id=user_id,
                        problem_id=q_id,
                        difficulty=difficulty
                    )
                    if reward_info:
                        result["reward_info"] = reward_info
                except Exception as e:
                    print(f"[HDL Arena] Warning: award_problem_completion error: {e}")

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        generic_msg = "An unexpected error occurred during evaluation."
        return jsonify({
            "ok": False,
            "error": {
                "code": "INTERNAL_JUDGE_ERROR",
                "message": generic_msg
            },
            "verdict": "INTERNAL_JUDGE_ERROR",
            "message": generic_msg,
            "console": generic_msg,
            "test_results": [],
            "stats": {"passed": 0, "total": 0, "exec_time_ms": 0}
        }), 500


@app.get("/api/user/progress")
def get_user_progress():
    """
    Returns interview platform progress:
    - solved_ids
    - attempted_ids
    - mistake_ids
    - bookmarks
    - coins
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in."}), 401

    progress = database.get_user_interview_progress(user["id"])
    coins_info = database.get_user_coins_info(user["id"])
    return jsonify({
        "status": "ok",
        "user_id": user["id"],
        "coins": coins_info.get("coins", 0.0),
        **progress
    })


@app.get("/api/submissions/<problem_id>")
def get_submissions(problem_id):
    user = get_current_user()
    if not user:
        return jsonify([])
    limit = int(request.args.get("limit", 20))
    records = database.get_submissions_for_problem(user["id"], problem_id, limit=limit)
    return jsonify(records)


@app.post("/api/drafts/<problem_id>")
def save_problem_draft(problem_id):
    user = get_current_user()
    user_id = user["id"] if user else 1
    data = request.get_json(silent=True) or {}
    files = data.get("files", {})
    database.save_draft(user_id, problem_id, files)
    return jsonify({"status": "saved", "problem_id": problem_id})


@app.get("/api/user/stats")
def get_stats():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in."}), 401
    stats = database.get_user_stats(user["id"], QUESTIONS_REGISTRY)
    return jsonify(stats)


@app.post("/api/user/bookmark")
def toggle_problem_bookmark():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized: Please log in to bookmark problems."}), 401
    data = request.get_json(silent=True) or {}
    problem_id = data.get("problem_id") or data.get("question_id")
    if not problem_id:
        return jsonify({"error": "Missing problem_id"}), 400

    bookmarked, all_bookmarks = database.toggle_bookmark(user["id"], problem_id)
    return jsonify({
        "problem_id": problem_id,
        "bookmarked": bookmarked,
        "all_bookmarks": all_bookmarks
    })


# Synchronize in-memory registry questions into Phase 1 persistent database tables
try:
    _synced, _errs, _details = database.sync_registry_to_db(QUESTIONS_REGISTRY)
    print(f"[HDL Arena] Synced {_synced} questions to database tables (errors: {_errs}).")
except Exception as _e:
    print(f"[HDL Arena] Warning: Question registry DB sync error: {_e}")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False,
    )
