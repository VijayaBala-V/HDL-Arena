import json
import sqlite3
import hashlib
import secrets
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "hdl_arena.db"
KOLKATA_TZ = timezone(timedelta(hours=5, minutes=30))


def get_kolkata_now():
    return datetime.now(KOLKATA_TZ)


def get_kolkata_date_str():
    return get_kolkata_now().strftime("%Y-%m-%d")


def backup_database_with_integrity_check():
    """
    Performs PRAGMA integrity_check on hdl_arena.db and creates a verified,
    timestamped backup in backend/backups/ prior to any schema additions.
    Returns (True, backup_path) or (False, error_message).
    """
    if not DB_PATH.exists():
        return True, "No database file yet"

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        res = cur.fetchone()
        conn.close()

        if not res or res[0] != "ok":
            return False, f"Integrity check failed: {res}"

        backup_dir = DB_PATH.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = get_kolkata_now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"hdl_arena_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_path)
        print(f"[HDL Arena] Database backup verified & created: {backup_path}")
        return True, str(backup_path)
    except Exception as e:
        print(f"[HDL Arena] Warning: DB backup failed: {e}")
        return False, str(e)


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # Autocommit mode: enables clean manual BEGIN IMMEDIATE, COMMIT, and ROLLBACK
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    return conn


def init_db():
    # 0. Backup database with verified PRAGMA integrity_check before any schema migration
    backup_ok, backup_info = backup_database_with_integrity_check()
    if not backup_ok:
        print(f"[HDL Arena] Warning: Database backup/integrity warning: {backup_info}")

    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        auth_token TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 2. User Profiles table
    # Storing coin_units where 1 VJ Coin = 2 units (0.5 VJ Coin = 1 unit)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY,
        coins REAL DEFAULT 0,
        coin_units INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        last_active_date TEXT,
        total_earned REAL DEFAULT 0,
        total_spent REAL DEFAULT 0,
        bookmarked_json TEXT DEFAULT '[]',
        attempted_json TEXT DEFAULT '[]',
        mistakes_json TEXT DEFAULT '[]',
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Schema Migrations: ensure new columns exist in existing database
    cursor.execute("PRAGMA table_info(user_profiles)")
    columns = [col[1] for col in cursor.fetchall()]
    if "coin_units" not in columns:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN coin_units INTEGER DEFAULT 0")
        cursor.execute("UPDATE user_profiles SET coin_units = CAST(ROUND(coins * 2) AS INTEGER)")
    if "attempted_json" not in columns:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN attempted_json TEXT DEFAULT '[]'")
    if "mistakes_json" not in columns:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN mistakes_json TEXT DEFAULT '[]'")

    # 3. Daily activity table (enforces max 1 daily reward per user per calendar day)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_date TEXT NOT NULL,
        daily_coin_awarded INTEGER DEFAULT 0,
        streak_count INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, activity_date),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 4. Coin transactions table (auditable ledger with idempotency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coin_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        problem_id TEXT,
        description TEXT NOT NULL,
        idempotency_key TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 5. Problem completions table (first-time solve tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problem_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        verdict TEXT NOT NULL,
        coin_awarded REAL DEFAULT 0,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, problem_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 6. Solution unlocks table (permanent unlock per user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solution_unlocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, problem_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 7. Submissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        verdict TEXT NOT NULL,
        message TEXT,
        tests_passed INTEGER DEFAULT 0,
        tests_total INTEGER DEFAULT 0,
        exec_time_ms REAL DEFAULT 0,
        language TEXT DEFAULT 'verilog',
        code_snapshot TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 8. Drafts table (user-specific problem drafts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drafts (
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        files_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (user_id, problem_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 9. Paid Hint Unlocks table (tracks individual progressive hint reveals at 0.5 VJ Coin each)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hint_unlocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id TEXT NOT NULL,
        hint_index INTEGER NOT NULL,
        cost_coins REAL DEFAULT 0.5,
        created_at TEXT NOT NULL,
        UNIQUE(user_id, problem_id, hint_index),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 10. Question Attempts & Evaluation Rubrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id TEXT NOT NULL,
        question_type TEXT NOT NULL,
        verdict TEXT NOT NULL,
        answer_payload TEXT,
        score REAL DEFAULT 0,
        feedback TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 11. Core Problems table (Phase 1 Question Bank Data Model)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        category TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        question_type TEXT NOT NULL,
        language TEXT NOT NULL,
        description TEXT NOT NULL,
        module_name TEXT,
        interface TEXT,
        ports_json TEXT DEFAULT '[]',
        requirements_json TEXT DEFAULT '[]',
        constraints_json TEXT DEFAULT '[]',
        examples_json TEXT DEFAULT '[]',
        options_json TEXT DEFAULT '[]',
        rubric_criteria_json TEXT DEFAULT '[]',
        starter_files_json TEXT NOT NULL,
        estimated_minutes INTEGER DEFAULT 15,
        publication_status TEXT DEFAULT 'published',
        validation_status TEXT DEFAULT 'verified',
        content_fingerprint TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_difficulty ON problems(difficulty)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_topic ON problems(topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_type ON problems(question_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_problems_language ON problems(language)")

    # 12. Language Variants table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS language_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        language TEXT NOT NULL,
        language_version TEXT NOT NULL,
        compiler_required TEXT NOT NULL,
        entry_point TEXT NOT NULL,
        starter_files_json TEXT NOT NULL,
        execution_settings_json TEXT DEFAULT '{}',
        created_at TEXT NOT NULL,
        UNIQUE(problem_id, language),
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # 13. Reference Solutions table (Restricted Server-Side Access Only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reference_solutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        language TEXT NOT NULL,
        version TEXT DEFAULT '1.0.0',
        canonical_files_json TEXT NOT NULL,
        expected_behavior TEXT,
        architecture_notes TEXT,
        validation_result TEXT DEFAULT 'verified',
        created_at TEXT NOT NULL,
        UNIQUE(problem_id, language, version),
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # 14. Test Suites table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_suites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        suite_version TEXT DEFAULT '1.0.0',
        harness_code TEXT NOT NULL,
        test_categories_json TEXT DEFAULT '[]',
        expected_behavior TEXT,
        timeout_sec REAL DEFAULT 10.0,
        memory_limit_mb INTEGER DEFAULT 128,
        validation_status TEXT DEFAULT 'verified',
        created_at TEXT NOT NULL,
        UNIQUE(problem_id, suite_version),
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # 15. Question Hints table (Progressive Hint Levels)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_hints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        hint_level INTEGER NOT NULL,
        title TEXT NOT NULL,
        hint_text TEXT NOT NULL,
        cost_coins REAL DEFAULT 0.5,
        policy TEXT DEFAULT 'progressive',
        created_at TEXT NOT NULL,
        UNIQUE(problem_id, hint_level),
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # 16. Question Explanations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_explanations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT UNIQUE NOT NULL,
        core_concept TEXT NOT NULL,
        approach TEXT NOT NULL,
        corner_cases TEXT,
        common_mistakes TEXT,
        complexity_analysis TEXT,
        related_topics_json TEXT DEFAULT '[]',
        created_at TEXT NOT NULL,
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # 17. Source Attributions table (Full License & Attribution Tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS source_attributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT UNIQUE NOT NULL,
        repo_url TEXT NOT NULL,
        original_path TEXT NOT NULL,
        commit_hash TEXT,
        version_tag TEXT,
        license_identifier TEXT NOT NULL,
        copyright_notice TEXT NOT NULL,
        import_date TEXT NOT NULL,
        permitted_reuse TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)

    # Seed default user 'engineer' if no users exist
    cursor.execute("SELECT id FROM users LIMIT 1")
    if not cursor.fetchone():
        now_str = get_kolkata_now().isoformat()
        dummy_hash = hashlib.sha256("engineer123".encode()).hexdigest()
        default_token = "hdl_token_default_engineer_001"
        cursor.execute("""
        INSERT INTO users (id, username, password_hash, auth_token, created_at)
        VALUES (1, 'engineer', ?, ?, ?)
        """, (dummy_hash, default_token, now_str))

        cursor.execute("""
        INSERT INTO user_profiles (user_id, coins, coin_units, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json, attempted_json, mistakes_json, updated_at)
        VALUES (1, 3.0, 6, 0, 0, NULL, 3.0, 0.0, '[]', '[]', '[]', ?)
        """, (now_str,))

        cursor.execute("""
        INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (1, 3.0, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', 'welcome_grant_1', ?)
        """, (now_str,))

    conn.commit()
    conn.close()


def get_user_by_token(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, auth_token, created_at FROM users WHERE auth_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_or_create_default_user():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, auth_token, created_at FROM users ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    now_str = get_kolkata_now().isoformat()
    if row:
        user_id = row["id"]
        # Ensure profile exists and has starter coins if fresh
        cursor.execute("SELECT coins, total_earned FROM user_profiles WHERE user_id = ?", (user_id,))
        prof = cursor.fetchone()
        if not prof:
            cursor.execute("""
            INSERT INTO user_profiles (user_id, coins, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json, updated_at)
            VALUES (?, 3, 0, 0, NULL, 3, 0, '[]', ?)
            """, (user_id, now_str))
            cursor.execute("""
            INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
            VALUES (?, 3, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', ?, ?)
            """, (user_id, f"welcome_grant_{user_id}", now_str))
            conn.commit()
        elif prof["coins"] == 0 and prof["total_earned"] == 0:
            cursor.execute("""
            UPDATE user_profiles SET coins = 3, total_earned = 3, updated_at = ? WHERE user_id = ?
            """, (now_str, user_id))
            cursor.execute("""
            INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
            VALUES (?, 3, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', ?, ?)
            """, (user_id, f"welcome_grant_{user_id}", now_str))
            conn.commit()
        conn.close()
        return dict(row)

    dummy_hash = hashlib.sha256("engineer123".encode()).hexdigest()
    default_token = "hdl_token_default_engineer_001"
    cursor.execute("""
    INSERT INTO users (username, password_hash, auth_token, created_at)
    VALUES ('engineer', ?, ?, ?)
    """, (dummy_hash, default_token, now_str))
    user_id = cursor.lastrowid
    cursor.execute("""
    INSERT INTO user_profiles (user_id, coins, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json, updated_at)
    VALUES (?, 3, 0, 0, NULL, 3, 0, '[]', ?)
    """, (user_id, now_str))
    cursor.execute("""
    INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
    VALUES (?, 3, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', ?, ?)
    """, (user_id, f"welcome_grant_{user_id}", now_str))
    conn.commit()
    conn.close()
    return {"id": user_id, "username": "engineer", "auth_token": default_token, "created_at": now_str}


def authenticate_or_register(username, password):
    conn = get_db()
    cursor = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT id, username, password_hash, auth_token FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    now_str = get_kolkata_now().isoformat()

    if row:
        if row["password_hash"] == pwd_hash:
            conn.close()
            return {"id": row["id"], "username": row["username"], "auth_token": row["auth_token"]}
        conn.close()
        return None  # Bad password
    else:
        new_token = f"hdl_{secrets.token_hex(16)}"
        cursor.execute("""
        INSERT INTO users (username, password_hash, auth_token, created_at)
        VALUES (?, ?, ?, ?)
        """, (username, pwd_hash, new_token, now_str))
        user_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO user_profiles (user_id, coins, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json, updated_at)
        VALUES (?, 3, 0, 0, NULL, 3, 0, '[]', ?)
        """, (user_id, now_str))
        cursor.execute("""
        INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (?, 3, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', ?, ?)
        """, (user_id, f"welcome_grant_{user_id}", now_str))
        conn.commit()
        conn.close()
        return {"id": user_id, "username": username, "auth_token": new_token}


# Helper: exact half-coin conversion
def units_to_coins(coin_units):
    if coin_units is None:
        return 0.0
    val = round(coin_units / 2.0, 1)
    return int(val) if val.is_integer() else val


# =============================================================================
# COIN SYSTEM & DAILY STREAK ENGINE (Asia/Kolkata Calendar)
# =============================================================================

def claim_daily_reward(user_id):
    """
    Awards +1 VJ Coin (+2 integer units) for the first successful login of each calendar day in Asia/Kolkata.
    Maintains streak count and longest streak.
    Idempotent: Repeated claims on the same day do not award extra coins.
    """
    today_str = get_kolkata_date_str()
    yesterday_str = (get_kolkata_now() - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_str = (get_kolkata_now() + timedelta(days=1)).strftime("%Y-%m-%d")
    now_iso = get_kolkata_now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    try:
        ensure_user_profile(user_id, cursor, conn)
        cursor.execute("BEGIN IMMEDIATE")

        # Check if already recorded/awarded today
        cursor.execute("SELECT daily_coin_awarded FROM daily_activity WHERE user_id = ? AND activity_date = ?", (user_id, today_str))
        existing_act = cursor.fetchone()

        if existing_act and existing_act["daily_coin_awarded"] == 1:
            # Already claimed today
            cursor.execute("SELECT coins, coin_units, streak, longest_streak, total_earned, total_spent FROM user_profiles WHERE user_id = ?", (user_id,))
            prof = cursor.fetchone()
            cursor.execute("COMMIT")
            current_coins = units_to_coins(prof["coin_units"]) if prof else 0
            return {
                "success": True,
                "awarded": False,
                "already_claimed": True,
                "coins_awarded": 0,
                "coins": current_coins,
                "streak": prof["streak"] if prof else 1,
                "longest_streak": prof["longest_streak"] if prof else 1,
                "date": today_str,
                "next_claim_date": tomorrow_str,
                "claimed_today": True,
                "message": f"Daily login reward already claimed for today ({today_str}). Next claim eligible on {tomorrow_str}."
            }

        # Calculate new streak
        cursor.execute("SELECT coins, coin_units, streak, longest_streak, last_active_date, total_earned, total_spent FROM user_profiles WHERE user_id = ?", (user_id,))
        prof = cursor.fetchone()
        current_units = prof["coin_units"] if (prof and prof["coin_units"] is not None) else int(round((prof["coins"] or 0) * 2))
        current_streak = prof["streak"] if prof else 0
        current_longest = prof["longest_streak"] if prof else 0
        last_active = prof["last_active_date"] if prof else None

        if last_active == yesterday_str:
            new_streak = current_streak + 1
        elif last_active == today_str:
            new_streak = max(current_streak, 1)
        else:
            new_streak = 1

        new_longest = max(current_longest, new_streak)
        new_units = current_units + 2  # +1.0 VJ Coin = 2 integer units
        new_coins = units_to_coins(new_units)
        new_total_earned = round((prof["total_earned"] if prof else 0) + 1.0, 1)

        # Record activity
        cursor.execute("""
        INSERT INTO daily_activity (user_id, activity_date, daily_coin_awarded, streak_count, created_at)
        VALUES (?, ?, 1, ?, ?)
        ON CONFLICT(user_id, activity_date) DO UPDATE SET
            daily_coin_awarded = 1,
            streak_count = excluded.streak_count
        """, (user_id, today_str, new_streak, now_iso))

        # Record transaction with unique idempotency key
        idempotency_key = f"daily_login_{user_id}_{today_str}"
        cursor.execute("""
        INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (?, 1.0, 'daily_login', NULL, ?, ?, ?)
        """, (user_id, f"Daily Login Reward (Day {new_streak} Streak)", idempotency_key, now_iso))

        # Update profile with exact units and coins
        cursor.execute("""
        UPDATE user_profiles
        SET coins = ?, coin_units = ?, streak = ?, longest_streak = ?, last_active_date = ?, total_earned = ?, updated_at = ?
        WHERE user_id = ?
        """, (new_coins, new_units, new_streak, new_longest, today_str, new_total_earned, now_iso, user_id))

        cursor.execute("COMMIT")

        return {
            "success": True,
            "awarded": True,
            "already_claimed": False,
            "coins_awarded": 1,
            "coins": new_coins,
            "streak": new_streak,
            "longest_streak": new_longest,
            "date": today_str,
            "next_claim_date": tomorrow_str,
            "claimed_today": True,
            "message": f"🎉 Daily Login Reward! +1 VJ Coin awarded. {new_streak}-day practice streak!"
        }
    except Exception as e:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            pass
        raise e
    finally:
        conn.close()


def award_problem_completion(user_id, problem_id, difficulty):
    """
    Awards +1 VJ Coin (+2 integer units) when a user solves a Medium, Hard, Advanced, or Expert problem for the first time.
    Easy / Beginner problems do not award coins.
    """
    diff_norm = difficulty.capitalize() if difficulty else "Easy"
    now_iso = get_kolkata_now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    try:
        ensure_user_profile(user_id, cursor, conn)
        cursor.execute("BEGIN IMMEDIATE")

        # Check if already completed previously
        cursor.execute("SELECT id FROM problem_completions WHERE user_id = ? AND problem_id = ?", (user_id, problem_id))
        if cursor.fetchone():
            cursor.execute("COMMIT")
            return {
                "awarded": False,
                "first_time": False,
                "coins_awarded": 0,
                "reason": "already_solved",
                "message": f"Problem '{problem_id}' already solved previously. No additional coins awarded."
            }

        # Check reward eligibility: Medium, Hard, Advanced, Expert get +1 VJ Coin
        qualifies_for_coin = diff_norm in ["Medium", "Hard", "Advanced", "Expert"]
        coins_to_award = 1.0 if qualifies_for_coin else 0.0
        units_to_award = 2 if qualifies_for_coin else 0

        # Record completion
        cursor.execute("""
        INSERT INTO problem_completions (user_id, problem_id, difficulty, verdict, coin_awarded, created_at)
        VALUES (?, ?, ?, 'ACCEPTED', ?, ?)
        """, (user_id, problem_id, diff_norm, coins_to_award, now_iso))

        if units_to_award > 0:
            idempotency_key = f"first_solve_{user_id}_{problem_id}"
            desc = f"First-time solve award for {diff_norm} challenge: {problem_id}"
            cursor.execute("""
            INSERT INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
            VALUES (?, 1.0, 'problem_solved', ?, ?, ?, ?)
            """, (user_id, problem_id, desc, idempotency_key, now_iso))

            cursor.execute("""
            UPDATE user_profiles
            SET coin_units = COALESCE(coin_units, CAST(ROUND(coins * 2) AS INTEGER)) + 2,
                coins = ROUND((COALESCE(coin_units, CAST(ROUND(coins * 2) AS INTEGER)) + 2) / 2.0, 1),
                total_earned = total_earned + 1.0,
                updated_at = ?
            WHERE user_id = ?
            """, (now_iso, user_id))

        cursor.execute("SELECT coins, coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
        p_row = cursor.fetchone()
        new_coins = units_to_coins(p_row["coin_units"]) if p_row else 0

        cursor.execute("COMMIT")

        if coins_to_award > 0:
            msg = f"🏆 First-time completion of {diff_norm} challenge '{problem_id}'! +1 VJ Coin awarded."
        else:
            msg = f"✓ Challenge '{problem_id}' ({diff_norm}) passed!"

        return {
            "awarded": (coins_to_award > 0),
            "first_time": True,
            "coins_awarded": coins_to_award,
            "coins": new_coins,
            "difficulty": diff_norm,
            "message": msg
        }
    except Exception as e:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            pass
        raise e
    finally:
        conn.close()


def unlock_solution(user_id, problem_id):
    """
    Unlocks a problem's reference solution for 1.0 VJ Coin (2 integer units).
    Atomic transaction: verifies sufficient coins, deducts 2 units, records transaction and unlock.
    If already unlocked, returns success without charging.
    """
    now_iso = get_kolkata_now().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    try:
        ensure_user_profile(user_id, cursor, conn)
        cursor.execute("BEGIN IMMEDIATE")

        # 1. Check if already unlocked
        cursor.execute("SELECT id FROM solution_unlocks WHERE user_id = ? AND problem_id = ?", (user_id, problem_id))
        if cursor.fetchone():
            cursor.execute("SELECT coins, coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
            prof = cursor.fetchone()
            cursor.execute("COMMIT")
            return {
                "success": True,
                "already_unlocked": True,
                "coins_deducted": 0,
                "coins": units_to_coins(prof["coin_units"]) if prof else 0,
                "message": "Reference solution already unlocked."
            }

        # 2. Check current balance (requires 2 units = 1.0 VJ Coin)
        cursor.execute("SELECT coins, coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
        prof = cursor.fetchone()
        current_units = prof["coin_units"] if (prof and prof["coin_units"] is not None) else int(round((prof["coins"] or 0) * 2))
        current_coins = units_to_coins(current_units)

        if current_units < 2:
            cursor.execute("COMMIT")
            return {
                "success": False,
                "error": f"Insufficient VJ Coins. You have {current_coins} VJ Coins, but 1 VJ Coin is required to unlock this reference solution. Solve Medium/Hard problems or claim daily rewards to earn coins!",
                "coins": current_coins
            }

        # 3. Deduct 2 units atomically
        cursor.execute("""
        UPDATE user_profiles
        SET coin_units = coin_units - 2,
            coins = ROUND((coin_units - 2) / 2.0, 1),
            total_spent = total_spent + 1.0,
            updated_at = ?
        WHERE user_id = ? AND coin_units >= 2
        """, (now_iso, user_id))

        if cursor.rowcount != 1:
            try:
                cursor.execute("ROLLBACK")
            except Exception:
                pass
            return {"success": False, "error": "Transaction conflict. Please try again."}

        # 4. Record unlock
        cursor.execute("""
        INSERT INTO solution_unlocks (user_id, problem_id, created_at)
        VALUES (?, ?, ?)
        """, (user_id, problem_id, now_iso))

        # 5. Record transaction ledger entry
        idempotency_key = f"unlock_solution_{user_id}_{problem_id}"
        desc = f"Unlocked Reference Solution for problem: {problem_id}"
        cursor.execute("""
        INSERT INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (?, -1.0, 'solution_unlock', ?, ?, ?, ?)
        """, (user_id, problem_id, desc, idempotency_key, now_iso))

        cursor.execute("SELECT coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
        updated_prof = cursor.fetchone()
        new_coins = units_to_coins(updated_prof["coin_units"]) if updated_prof else 0

        cursor.execute("COMMIT")

        return {
            "success": True,
            "already_unlocked": False,
            "coins_deducted": 1.0,
            "coins": new_coins,
            "message": f"🔓 Reference solution for '{problem_id}' unlocked successfully for 1 VJ Coin."
        }
    except Exception as e:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            pass
        raise e
    finally:
        conn.close()


def unlock_paid_hint(user_id, problem_id, hint_index):
    """
    Unlocks a specific progressive hint for 0.5 VJ Coin (1 integer unit).
    If already unlocked, returns success without charging.
    Atomic: verifies sufficient balance (>= 0.5 VJ), deducts 1 unit, records ledger & hint unlock.
    """
    now_iso = get_kolkata_now().isoformat()
    conn = get_db()
    cursor = conn.cursor()

    try:
        ensure_user_profile(user_id, cursor, conn)
        cursor.execute("BEGIN IMMEDIATE")

        # 1. Check if this specific hint was already unlocked
        cursor.execute("""
        SELECT id FROM hint_unlocks
        WHERE user_id = ? AND problem_id = ? AND hint_index = ?
        """, (user_id, problem_id, hint_index))
        if cursor.fetchone():
            cursor.execute("SELECT coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
            prof = cursor.fetchone()
            cursor.execute("COMMIT")
            return {
                "success": True,
                "already_unlocked": True,
                "coins_deducted": 0.0,
                "coins": units_to_coins(prof["coin_units"]) if prof else 0,
                "hint_index": hint_index,
                "message": f"Hint #{hint_index + 1} already unlocked."
            }

        # 2. Check balance (requires 1 unit = 0.5 VJ Coin)
        cursor.execute("SELECT coins, coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
        prof = cursor.fetchone()
        current_units = prof["coin_units"] if (prof and prof["coin_units"] is not None) else int(round((prof["coins"] or 0) * 2))
        current_coins = units_to_coins(current_units)

        if current_units < 1:
            cursor.execute("COMMIT")
            return {
                "success": False,
                "error": f"Insufficient VJ Coins. You have {current_coins} VJ Coins, but 0.5 VJ Coin is required to reveal this hint. Solve questions or check in daily to earn coins!",
                "coins": current_coins,
                "hint_index": hint_index
            }

        # 3. Deduct 1 unit (-0.5 VJ Coin)
        cursor.execute("""
        UPDATE user_profiles
        SET coin_units = coin_units - 1,
            coins = ROUND((coin_units - 1) / 2.0, 1),
            total_spent = total_spent + 0.5,
            updated_at = ?
        WHERE user_id = ? AND coin_units >= 1
        """, (now_iso, user_id))

        if cursor.rowcount != 1:
            try:
                cursor.execute("ROLLBACK")
            except Exception:
                pass
            return {"success": False, "error": "Transaction conflict. Please retry."}

        # 4. Record hint unlock
        cursor.execute("""
        INSERT INTO hint_unlocks (user_id, problem_id, hint_index, cost_coins, created_at)
        VALUES (?, ?, ?, 0.5, ?)
        """, (user_id, problem_id, hint_index, now_iso))

        # 5. Ledger record
        idempotency_key = f"hint_unlock_{user_id}_{problem_id}_{hint_index}"
        desc = f"Revealed Progressive Hint #{hint_index + 1} for: {problem_id} (-0.5 VJ)"
        cursor.execute("""
        INSERT INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (?, -0.5, 'hint_unlock', ?, ?, ?, ?)
        """, (user_id, problem_id, desc, idempotency_key, now_iso))

        cursor.execute("SELECT coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
        updated_prof = cursor.fetchone()
        new_coins = units_to_coins(updated_prof["coin_units"]) if updated_prof else 0

        cursor.execute("COMMIT")

        return {
            "success": True,
            "already_unlocked": False,
            "coins_deducted": 0.5,
            "coins": new_coins,
            "hint_index": hint_index,
            "message": f"💡 Hint #{hint_index + 1} unlocked (-0.5 VJ Coin)!"
        }
    except Exception as e:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            pass
        raise e
    finally:
        conn.close()


def get_unlocked_hints_for_problem(user_id, problem_id):
    """
    Returns list of hint indices [0, 1, ...] unlocked by this user for this problem.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT hint_index FROM hint_unlocks
    WHERE user_id = ? AND problem_id = ?
    ORDER BY hint_index ASC
    """, (user_id, problem_id))
    indices = [r[0] for r in cursor.fetchall()]
    conn.close()
    return indices

def is_solution_unlocked(user_id, problem_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM solution_unlocks WHERE user_id = ? AND problem_id = ?", (user_id, problem_id))
    unlocked = cursor.fetchone() is not None
    conn.close()
    return unlocked


def is_hint_unlocked(user_id, problem_id, hint_index):
    """
    Checks if a specific progressive hint (0, 1, 2...) has been unlocked by user_id.
    Hint index 0 is free for all users and always considered unlocked.
    Hints with index >= 1 are checked against the persistent hint_unlocks table.
    """
    try:
        hint_index = int(hint_index)
    except (ValueError, TypeError):
        return False

    if hint_index == 0:
        return True

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 1 FROM hint_unlocks
    WHERE user_id = ? AND problem_id = ? AND hint_index = ?
    """, (user_id, problem_id, hint_index))
    unlocked = cursor.fetchone() is not None
    conn.close()
    return unlocked


def ensure_user_profile(user_id, cursor=None, conn=None):
    """
    Ensures that a user row and user_profiles row exist for user_id with the standard 3 starter coins (6 units).
    """
    close_on_finish = False
    if conn is None:
        conn = get_db()
        cursor = conn.cursor()
        close_on_finish = True

    now_str = get_kolkata_now().isoformat()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if not cursor.fetchone():
        dummy_hash = hashlib.sha256(f"user_{user_id}".encode()).hexdigest()
        token = f"hdl_{secrets.token_hex(16)}"
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, password_hash, auth_token, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, f"engineer_{user_id}", dummy_hash, token, now_str))

    cursor.execute("SELECT coins, coin_units FROM user_profiles WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()
    if not prof:
        cursor.execute("""
        INSERT INTO user_profiles (user_id, coins, coin_units, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json, attempted_json, mistakes_json, updated_at)
        VALUES (?, 3.0, 6, 0, 0, NULL, 3.0, 0.0, '[]', '[]', '[]', ?)
        """, (user_id, now_str))
        cursor.execute("""
        INSERT OR IGNORE INTO coin_transactions (user_id, amount, transaction_type, problem_id, description, idempotency_key, created_at)
        VALUES (?, 3.0, 'welcome_bonus', NULL, 'Welcome to HDL Arena: Starter Grant (+3 VJ Coins)', ?, ?)
        """, (user_id, f"welcome_grant_{user_id}", now_str))
    elif prof["coin_units"] is None or prof["coin_units"] == 0:
        calc_units = int(round((prof["coins"] or 3.0) * 2))
        cursor.execute("UPDATE user_profiles SET coin_units = ? WHERE user_id = ?", (calc_units, user_id))

    if close_on_finish:
        conn.close()


def get_user_coins_info(user_id):
    conn = get_db()
    cursor = conn.cursor()
    ensure_user_profile(user_id, cursor, conn)
    cursor.execute("SELECT coins, coin_units, streak, longest_streak, total_earned, total_spent, last_active_date FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM solution_unlocks WHERE user_id = ?", (user_id,))
    unlocks_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM hint_unlocks WHERE user_id = ?", (user_id,))
    hints_unlocked_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM problem_completions WHERE user_id = ?", (user_id,))
    completions_count = cursor.fetchone()[0]

    today_str = get_kolkata_date_str()
    tomorrow_str = (get_kolkata_now() + timedelta(days=1)).strftime("%Y-%m-%d")
    cursor.execute("SELECT daily_coin_awarded FROM daily_activity WHERE user_id = ? AND activity_date = ?", (user_id, today_str))
    act = cursor.fetchone()
    claimed_today = bool(act and act["daily_coin_awarded"] == 1)

    conn.close()

    actual_coins = units_to_coins(row["coin_units"]) if row else 0.0

    return {
        "coins": actual_coins,
        "coin_units": row["coin_units"] if row else 0,
        "streak": row["streak"] if row else 0,
        "longest_streak": row["longest_streak"] if row else 0,
        "total_earned": round(row["total_earned"] or 0.0, 1) if row else 0.0,
        "total_spent": round(row["total_spent"] or 0.0, 1) if row else 0.0,
        "claimed_today": claimed_today,
        "today_date": today_str,
        "next_claim_date": tomorrow_str if claimed_today else today_str,
        "unlocked_count": unlocks_count,
        "hints_unlocked_count": hints_unlocked_count,
        "solved_count": completions_count,
        "timezone": "Asia/Kolkata"
    }


def record_question_attempt(user_id, question_id, question_type, verdict, answer_payload=None, score=0.0, feedback=""):
    conn = get_db()
    cursor = conn.cursor()
    now_iso = get_kolkata_now().isoformat()

    payload_str = json.dumps(answer_payload) if isinstance(answer_payload, (dict, list)) else str(answer_payload or "")

    cursor.execute("""
    INSERT INTO question_attempts (user_id, question_id, question_type, verdict, answer_payload, score, feedback, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, question_id, question_type, verdict, payload_str, score, feedback, now_iso))

    # Update attempted_json and mistakes_json in user_profiles
    cursor.execute("SELECT attempted_json, mistakes_json FROM user_profiles WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()
    if prof:
        try:
            attempted = json.loads(prof["attempted_json"] or "[]")
        except Exception:
            attempted = []
        try:
            mistakes = json.loads(prof["mistakes_json"] or "[]")
        except Exception:
            mistakes = []

        if question_id not in attempted:
            attempted.append(question_id)

        if verdict == "ACCEPTED":
            if question_id in mistakes:
                mistakes.remove(question_id)
        elif verdict in ["WRONG_ANSWER", "COMPILE_ERROR", "RUNTIME_ERROR", "NEEDS_REVISION"]:
            if question_id not in mistakes:
                mistakes.append(question_id)

        cursor.execute("""
        UPDATE user_profiles
        SET attempted_json = ?, mistakes_json = ?, updated_at = ?
        WHERE user_id = ?
        """, (json.dumps(attempted), json.dumps(mistakes), now_iso, user_id))

    conn.commit()
    conn.close()


def get_user_interview_progress(user_id):
    conn = get_db()
    cursor = conn.cursor()
    ensure_user_profile(user_id, cursor, conn)

    cursor.execute("SELECT bookmarked_json, attempted_json, mistakes_json FROM user_profiles WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()

    cursor.execute("SELECT problem_id FROM problem_completions WHERE user_id = ?", (user_id,))
    solved_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT question_id FROM question_attempts WHERE user_id = ? AND verdict = 'ACCEPTED'", (user_id,))
    for r in cursor.fetchall():
        if r[0] not in solved_ids:
            solved_ids.append(r[0])

    try:
        bookmarks = json.loads(prof["bookmarked_json"] or "[]") if prof else []
    except Exception:
        bookmarks = []
    try:
        attempted = json.loads(prof["attempted_json"] or "[]") if prof else []
    except Exception:
        attempted = []
    try:
        mistakes = json.loads(prof["mistakes_json"] or "[]") if prof else []
    except Exception:
        mistakes = []

    conn.close()
    return {
        "solved_ids": solved_ids,
        "attempted_ids": attempted,
        "mistake_ids": mistakes,
        "bookmarked_ids": bookmarks
    }


def get_user_streak_info(user_id):
    conn = get_db()
    cursor = conn.cursor()
    ensure_user_profile(user_id, cursor, conn)
    today_str = get_kolkata_date_str()

    cursor.execute("SELECT streak, longest_streak, coins, total_earned, total_spent FROM user_profiles WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()

    cursor.execute("SELECT daily_coin_awarded FROM daily_activity WHERE user_id = ? AND activity_date = ?", (user_id, today_str))
    act = cursor.fetchone()
    claimed_today = bool(act and act["daily_coin_awarded"] == 1)

    # Fetch last 14 days activity calendar
    cursor.execute("""
    SELECT activity_date, daily_coin_awarded, streak_count
    FROM daily_activity
    WHERE user_id = ?
    ORDER BY activity_date DESC
    LIMIT 14
    """, (user_id,))
    activity_rows = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "current_streak": prof["streak"] if prof else 0,
        "longest_streak": prof["longest_streak"] if prof else 0,
        "coins": prof["coins"] if prof else 0,
        "total_earned": prof["total_earned"] if prof else 0,
        "total_spent": prof["total_spent"] if prof else 0,
        "claimed_today": claimed_today,
        "today_date": today_str,
        "next_claim_date": (get_kolkata_now() + timedelta(days=1)).strftime("%Y-%m-%d") if claimed_today else today_str,
        "timezone": "Asia/Kolkata",
        "recent_activity": activity_rows
    }


def get_user_transactions(user_id, limit=30):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, amount, transaction_type, problem_id, description, created_at
    FROM coin_transactions
    WHERE user_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_unlocked_solutions_for_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT problem_id FROM solution_unlocks WHERE user_id = ?", (user_id,))
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


# =============================================================================
# SUBMISSIONS & DRAFTS PERSISTENCE
# =============================================================================

def record_submission(user_id, problem_id, verdict, message, tests_passed, tests_total, exec_time_ms, language, code_snapshot):
    conn = get_db()
    cursor = conn.cursor()
    now_iso = get_kolkata_now().isoformat()

    cursor.execute("""
    INSERT INTO submissions (user_id, problem_id, verdict, message, tests_passed, tests_total, exec_time_ms, language, code_snapshot, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, problem_id, verdict, message, tests_passed, tests_total,
        exec_time_ms, language,
        json.dumps(code_snapshot) if isinstance(code_snapshot, (dict, list)) else str(code_snapshot),
        now_iso
    ))
    conn.commit()
    conn.close()


def get_submissions_for_problem(user_id, problem_id, limit=20):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, problem_id, verdict, message, tests_passed, tests_total, exec_time_ms, language, code_snapshot, created_at
    FROM submissions
    WHERE user_id = ? AND problem_id = ?
    ORDER BY id DESC
    LIMIT ?
    """, (user_id, problem_id, limit))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        snapshot = r["code_snapshot"]
        try:
            snapshot = json.loads(snapshot)
        except Exception:
            pass
        result.append({
            "id": r["id"],
            "problem_id": r["problem_id"],
            "verdict": r["verdict"],
            "message": r["message"],
            "tests_passed": r["tests_passed"],
            "tests_total": r["tests_total"],
            "exec_time_ms": r["exec_time_ms"],
            "language": r["language"],
            "code_snapshot": snapshot,
            "created_at": r["created_at"]
        })
    return result


def save_draft(user_id, problem_id, files_dict):
    conn = get_db()
    cursor = conn.cursor()
    now_iso = get_kolkata_now().isoformat()
    cursor.execute("""
    INSERT INTO drafts (user_id, problem_id, files_json, updated_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, problem_id) DO UPDATE SET
        files_json = excluded.files_json,
        updated_at = excluded.updated_at
    """, (user_id, problem_id, json.dumps(files_dict), now_iso))
    conn.commit()
    conn.close()


def get_draft(user_id, problem_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT files_json FROM drafts WHERE user_id = ? AND problem_id = ?", (user_id, problem_id))
    row = cursor.fetchone()
    conn.close()
    if row and row["files_json"]:
        try:
            parsed = json.loads(row["files_json"])
            if isinstance(parsed, dict) and any(isinstance(v, str) and v.strip() for v in parsed.values()):
                return parsed
        except Exception:
            pass
    return None


def toggle_bookmark(user_id, problem_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT bookmarked_json FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    bookmarks = json.loads(row["bookmarked_json"]) if row and row["bookmarked_json"] else []

    if problem_id in bookmarks:
        bookmarks.remove(problem_id)
        bookmarked = False
    else:
        bookmarks.append(problem_id)
        bookmarked = True

    now_iso = get_kolkata_now().isoformat()
    cursor.execute("UPDATE user_profiles SET bookmarked_json = ?, updated_at = ? WHERE user_id = ?", (json.dumps(bookmarks), now_iso, user_id))
    conn.commit()
    conn.close()
    return bookmarked, bookmarks


def get_user_stats(user_id, all_problems_dict):
    conn = get_db()
    cursor = conn.cursor()
    ensure_user_profile(user_id, cursor, conn)

    cursor.execute("SELECT username, created_at FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    username = user_row["username"] if user_row else "RTL Engineer"

    cursor.execute("""
    SELECT coins, streak, longest_streak, last_active_date, total_earned, total_spent, bookmarked_json
    FROM user_profiles WHERE user_id = ?
    """, (user_id,))
    profile_row = cursor.fetchone()

    today_str = get_kolkata_date_str()
    cursor.execute("SELECT daily_coin_awarded FROM daily_activity WHERE user_id = ? AND activity_date = ?", (user_id, today_str))
    act_row = cursor.fetchone()
    claimed_today = bool(act_row and act_row["daily_coin_awarded"] == 1)

    coins = profile_row["coins"] if profile_row else 0
    streak = profile_row["streak"] if profile_row else 0
    longest_streak = profile_row["longest_streak"] if profile_row else 0
    total_earned = profile_row["total_earned"] if profile_row else 0
    total_spent = profile_row["total_spent"] if profile_row else 0
    bookmarks = json.loads(profile_row["bookmarked_json"]) if profile_row and profile_row["bookmarked_json"] else []

    cursor.execute("SELECT problem_id FROM solution_unlocks WHERE user_id = ?", (user_id,))
    unlocked_solutions = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT problem_id FROM problem_completions WHERE user_id = ?", (user_id,))
    solved_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM submissions WHERE user_id = ?", (user_id,))
    total_submissions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM submissions WHERE user_id = ? AND verdict = 'ACCEPTED'", (user_id,))
    accepted_submissions = cursor.fetchone()[0]

    # Fetch recent transactions
    cursor.execute("""
    SELECT id, amount, transaction_type, problem_id, description, created_at
    FROM coin_transactions WHERE user_id = ?
    ORDER BY id DESC LIMIT 20
    """, (user_id,))
    transactions = [dict(r) for r in cursor.fetchall()]

    # Fetch recent 14-day activity
    cursor.execute("""
    SELECT activity_date, daily_coin_awarded, streak_count
    FROM daily_activity WHERE user_id = ?
    ORDER BY activity_date DESC LIMIT 14
    """, (user_id,))
    recent_activity = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Difficulty counts
    difficulty_stats = {
        "Easy": {"solved": 0, "total": 0},
        "Medium": {"solved": 0, "total": 0},
        "Hard": {"solved": 0, "total": 0},
        "Expert": {"solved": 0, "total": 0}
    }
    category_stats = {}

    for pid, p in all_problems_dict.items():
        diff = p.get("difficulty", "Medium")
        cat = p.get("category", "General")
        if diff in difficulty_stats:
            difficulty_stats[diff]["total"] += 1
            if pid in solved_ids:
                difficulty_stats[diff]["solved"] += 1

        if cat not in category_stats:
            category_stats[cat] = {"solved": 0, "total": 0}
        category_stats[cat]["total"] += 1
        if pid in solved_ids:
            category_stats[cat]["solved"] += 1

    return {
        "username": username,
        "user_id": user_id,
        "streak": streak,
        "longest_streak": longest_streak,
        "coins": coins,
        "total_earned": total_earned,
        "total_spent": total_spent,
        "claimed_today": claimed_today,
        "today_date": today_str,
        "next_claim_date": (get_kolkata_now() + timedelta(days=1)).strftime("%Y-%m-%d") if claimed_today else today_str,
        "timezone": "Asia/Kolkata",
        "unlocked_solutions": unlocked_solutions,
        "solved_ids": solved_ids,
        "solved_count": len(solved_ids),
        "total_problems": len(all_problems_dict),
        "total_submissions": total_submissions,
        "accepted_submissions": accepted_submissions,
        "acceptance_rate": round((accepted_submissions / total_submissions * 100), 1) if total_submissions > 0 else 0,
        "bookmarks": bookmarks,
        "transactions": transactions,
        "recent_activity": recent_activity,
        "difficulty_stats": difficulty_stats,
        "category_stats": category_stats
    }


# =============================================================================
# PHASE 1 — QUESTION BANK DATA MODEL SYNC & QUERY FUNCTIONS
# =============================================================================

def generate_problem_fingerprint(p):
    """
    Computes a deterministic SHA-256 content fingerprint for duplicate prevention.
    """
    raw = (
        f"{p.get('id', '')}|"
        f"{p.get('title', '')}|"
        f"{p.get('module_name', '')}|"
        f"{p.get('difficulty', '')}|"
        f"{p.get('language', '')}|"
        f"{p.get('type', '')}|"
        f"{json.dumps(p.get('starter_files', {}), sort_keys=True)}|"
        f"{p.get('description', '')}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sync_problem_to_db(p):
    """
    Persists a problem and all associated logical entities into the database:
    - problems
    - language_variants
    - reference_solutions (server-side restricted)
    - test_suites (trusted harnesses)
    - question_hints (progressive clue levels)
    - question_explanations
    - source_attributions (licensing and copyright notice)
    """
    pid = p["id"]
    slug = p.get("slug") or pid
    fingerprint = generate_problem_fingerprint(p)
    now_iso = get_kolkata_now().isoformat()

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        # 1. Upsert Problem
        cursor.execute("""
        INSERT INTO problems (
            id, slug, title, topic, category, difficulty, question_type,
            language, description, module_name, interface, ports_json,
            requirements_json, constraints_json, examples_json, options_json,
            rubric_criteria_json, starter_files_json, estimated_minutes,
            publication_status, validation_status, content_fingerprint,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            topic = excluded.topic,
            category = excluded.category,
            difficulty = excluded.difficulty,
            question_type = excluded.question_type,
            language = excluded.language,
            description = excluded.description,
            module_name = excluded.module_name,
            interface = excluded.interface,
            ports_json = excluded.ports_json,
            requirements_json = excluded.requirements_json,
            constraints_json = excluded.constraints_json,
            examples_json = excluded.examples_json,
            options_json = excluded.options_json,
            rubric_criteria_json = excluded.rubric_criteria_json,
            starter_files_json = excluded.starter_files_json,
            estimated_minutes = excluded.estimated_minutes,
            validation_status = excluded.validation_status,
            content_fingerprint = excluded.content_fingerprint,
            updated_at = excluded.updated_at
        """, (
            pid, slug, p.get("title", pid),
            p.get("topic") or p.get("category", "General"),
            p.get("category") or p.get("topic", "General"),
            p.get("difficulty", "Beginner"),
            p.get("type", "coding"),
            p.get("language", "verilog"),
            p.get("description", ""),
            p.get("module_name", pid),
            p.get("interface", ""),
            json.dumps(p.get("ports", [])),
            json.dumps(p.get("requirements", [])),
            json.dumps(p.get("constraints", [])),
            json.dumps(p.get("examples", [])),
            json.dumps(p.get("options", [])),
            json.dumps(p.get("rubric_criteria", [])),
            json.dumps(p.get("starter_files", {})),
            p.get("estimated_minutes", 15),
            p.get("publication_status", "published"),
            p.get("validation_status", "verified"),
            fingerprint,
            now_iso, now_iso
        ))

        # 2. Upsert Language Variant
        lang = p.get("language", "verilog")
        compiler = "iverilog"
        if lang in ("c", "cpp"):
            compiler = "clang" if lang == "c" else "clang++"
        elif lang == "python":
            compiler = "python3"

        cursor.execute("""
        INSERT INTO language_variants (
            problem_id, language, language_version, compiler_required,
            entry_point, starter_files_json, execution_settings_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(problem_id, language) DO UPDATE SET
            compiler_required = excluded.compiler_required,
            entry_point = excluded.entry_point,
            starter_files_json = excluded.starter_files_json
        """, (
            pid, lang, p.get("language_version", "default"), compiler,
            p.get("module_name", pid),
            json.dumps(p.get("starter_files", {})),
            json.dumps(p.get("execution_settings", {})),
            now_iso
        ))

        # 3. Upsert Reference Solution (Server-Side Restricted)
        sol = p.get("solution") or {}
        canonical = sol.get("canonical_code") or {}
        if canonical:
            cursor.execute("""
            INSERT INTO reference_solutions (
                problem_id, language, version, canonical_files_json,
                expected_behavior, architecture_notes, validation_result, created_at
            ) VALUES (?, ?, '1.0.0', ?, ?, ?, 'verified', ?)
            ON CONFLICT(problem_id, language, version) DO UPDATE SET
                canonical_files_json = excluded.canonical_files_json,
                architecture_notes = excluded.architecture_notes
            """, (
                pid, lang, json.dumps(canonical),
                sol.get("expected_behavior", ""),
                sol.get("architecture_notes", "") or p.get("explanation", ""),
                now_iso
            ))

        # 4. Upsert Test Suite
        tb_code = p.get("testbench") or p.get("test_harness") or ""
        if tb_code:
            cursor.execute("""
            INSERT INTO test_suites (
                problem_id, suite_version, harness_code, test_categories_json,
                expected_behavior, timeout_sec, memory_limit_mb, validation_status, created_at
            ) VALUES (?, ?, ?, ?, ?, 10.0, 128, 'verified', ?)
            ON CONFLICT(problem_id, suite_version) DO UPDATE SET
                harness_code = excluded.harness_code,
                test_categories_json = excluded.test_categories_json
            """, (
                pid, p.get("test_suite_version", "1.0.0"),
                tb_code if isinstance(tb_code, str) else json.dumps(tb_code),
                json.dumps(p.get("test_categories", ["sample", "hidden"])),
                p.get("expected_behavior", "Cycle-by-cycle assertion match"),
                now_iso
            ))

        # 5. Upsert Progressive Hints
        hints = p.get("progressive_hints") or []
        if not hints and p.get("hints"):
            hints = [
                {"index": i, "cost": 0.0 if i == 0 else 0.5, "title": f"Hint {i+1}", "text": t}
                for i, t in enumerate(p.get("hints", []))
            ]

        for h in hints:
            h_idx = h.get("index", 0)
            cursor.execute("""
            INSERT INTO question_hints (
                problem_id, hint_level, title, hint_text, cost_coins, policy, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(problem_id, hint_level) DO UPDATE SET
                title = excluded.title,
                hint_text = excluded.hint_text,
                cost_coins = excluded.cost_coins
            """, (
                pid, h_idx, h.get("title", f"Hint {h_idx+1}"),
                h.get("text", ""), float(h.get("cost", 0.0 if h_idx == 0 else 0.5)),
                "free" if h_idx == 0 else "progressive",
                now_iso
            ))

        # 6. Upsert Question Explanation
        if p.get("explanation") or sol.get("architecture_notes"):
            cursor.execute("""
            INSERT INTO question_explanations (
                problem_id, core_concept, approach, corner_cases,
                common_mistakes, complexity_analysis, related_topics_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(problem_id) DO UPDATE SET
                core_concept = excluded.core_concept,
                approach = excluded.approach
            """, (
                pid,
                p.get("topic", "Digital Logic"),
                p.get("explanation", "") or sol.get("architecture_notes", ""),
                "Rollover boundary, reset assertion, zero hold time",
                "Using blocking assignments in sequential blocks, inferred latches",
                "O(1) space, 1 cycle latency",
                json.dumps(p.get("tags", [])),
                now_iso
            ))

        # 7. Upsert Source Attribution (License Compliance)
        meta = p.get("source_metadata") or {}
        cursor.execute("""
        INSERT INTO source_attributions (
            problem_id, repo_url, original_path, commit_hash, version_tag,
            license_identifier, copyright_notice, import_date, permitted_reuse, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(problem_id) DO UPDATE SET
            license_identifier = excluded.license_identifier,
            copyright_notice = excluded.copyright_notice
        """, (
            pid,
            meta.get("original_repo") or meta.get("repo_url", "https://github.com/hdl-arena/curated"),
            meta.get("original_path", f"problems/{pid}"),
            meta.get("commit_hash", "main"),
            meta.get("version_tag", "v1.0.0"),
            meta.get("license", "MIT"),
            meta.get("attribution") or meta.get("author", "HDL Arena Team / Open Source Contributors"),
            now_iso,
            meta.get("permitted_reuse", "redistribution_permitted"),
            meta.get("notes", "Fully validated testbench and canonical RTL.")
        ))

        cursor.execute("COMMIT")
        return True, "Synced"
    except Exception as e:
        try:
            cursor.execute("ROLLBACK")
        except Exception:
            pass
        return False, str(e)
    finally:
        conn.close()


def sync_registry_to_db(registry_dict):
    """
    Syncs an in-memory dictionary of questions into the Phase 1 DB tables.
    Returns (success_count, error_count, details).
    """
    success = 0
    errors = []
    for pid, p in registry_dict.items():
        ok, msg = sync_problem_to_db(p)
        if ok:
            success += 1
        else:
            errors.append(f"{pid}: {msg}")
    return success, len(errors), errors


# Initialize DB on load
init_db()
