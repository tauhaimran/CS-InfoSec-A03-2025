import argparse
import csv
from pathlib import Path
from datetime import datetime

from werkzeug.security import generate_password_hash

from database import DB_PATH, get_connection
from flag_cipher import encrypt_flag, hash_flag

try:
    from flag_payloads import PLAINTEXT_FLAGS
except ImportError:
    PLAINTEXT_FLAGS = []

LEADERBOARD_PLAYERS = [
    ("BTL23001", "Ada Lovelace", 1200),
    ("BTL23002", "Grace Hopper", 1180),
    ("BTL23003", "Alan Turing", 1165),
    ("BTL23004", "Annie Easley", 1130),
]

CONTRACTS = [
    ("Monarch Cyber", "Red-team readiness exercise", 85000, "VPN creds stored under vault entry v-992"),
    ("Helios Bank", "Mobile app pen test", 64000, "Data room URL: https://helios.example/deal"),
    ("Rapid Rail", "SCADA hardening review", 120000, "Flag stored in confidential appendix C"),
]

SHIPMENTS = [
    ("ZX-1001", "Red Cell Toolkit", 1),
    ("ZX-1002", "Training Badges", 0),
    ("ZX-1337", "Incident playbook", 1),
]

ADMINS = [
    ("root", "4ck-potato!"),
]

def bootstrap_schema(conn):
    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                points INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE NOT NULL,
                code TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                description TEXT
            );

            -- Separate table for SQLI_BASIC challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS player_secrets (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                secret_token TEXT NOT NULL,
                reward_points INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Separate table for SQLI_ADV challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS client_vault (
                vault_id INTEGER PRIMARY KEY AUTOINCREMENT,
                encrypted_data TEXT NOT NULL,
                access_level INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Separate table for SQLI_BLIND challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS access_keys (
                key_id INTEGER PRIMARY KEY AUTOINCREMENT,
                auth_token TEXT NOT NULL,
                status_code INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Separate table for XSS challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS message_vault (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                hidden_content TEXT NOT NULL,
                priority_level INTEGER DEFAULT 0,
                message_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Separate table for CSRF challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS session_tokens (
                token_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_data TEXT NOT NULL,
                token_status INTEGER DEFAULT 0,
                token_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Separate table for STEG challenge (isolated from others)
            CREATE TABLE IF NOT EXISTS image_metadata (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                embedded_data TEXT NOT NULL,
                image_type INTEGER DEFAULT 0,
                metadata_info TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                flag_id INTEGER,
                category TEXT,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                points INTEGER DEFAULT 0,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(flag_id) REFERENCES flags(id)
            );
            
            -- Create unique indexes for preventing duplicate submissions
            CREATE UNIQUE INDEX IF NOT EXISTS idx_submissions_flag 
                ON submissions(student_id, flag_id) WHERE flag_id IS NOT NULL;
            CREATE UNIQUE INDEX IF NOT EXISTS idx_submissions_category 
                ON submissions(student_id, category) WHERE category IS NOT NULL;

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            );

            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT UNIQUE NOT NULL,
                scope TEXT NOT NULL,
                budget INTEGER DEFAULT 0,
                confidential_notes TEXT
            );

            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT UNIQUE NOT NULL,
                destination TEXT,
                delivered INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS student_stats (
                student_id INTEGER PRIMARY KEY,
                total_points INTEGER DEFAULT 0,
                total_captures INTEGER DEFAULT 0,
                FOREIGN KEY(student_id) REFERENCES students(id)
            );
            """
        )


def ensure_flag_hash_column(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(flags)")}
    if "code_hash" not in columns:
        conn.execute("ALTER TABLE flags ADD COLUMN code_hash TEXT DEFAULT ''")


def seed_flags(conn):
    """Flags table is now empty - all flags are in isolated tables.
    This function is kept for backward compatibility but doesn't seed anything.
    """
    ensure_flag_hash_column(conn)
    # All flags are now in isolated tables, not in flags table
    pass


def seed_sqli_basic_flag(conn):
    """Seed SQLI_BASIC flag into isolated player_secrets table."""
    if not PLAINTEXT_FLAGS:
        return
    sqli_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "SQLI"), None)
    if sqli_flag:
        _, code, _ = sqli_flag
        with conn:
            # Clear and insert flag with dummy data to confuse sqlmap
            conn.execute("DELETE FROM player_secrets")
            conn.execute(
                """
                INSERT INTO player_secrets (secret_token, reward_points)
                VALUES (?, ?)
                """,
                (encrypt_flag(code), 999),
            )
            # Add realistic dummy flags to confuse students and automated tools
            dummy_flags = [
                "FLAG{Trust_me_its_ture_1}",
                "FLAG{Trust_me_its_ture_2}",
                "FLAG{Trust_me_its_false_1}",
                "FLAG{Trust_me_its_false_2}",
                "FLAG{This_is_not_the_flag}",
            ]
            for i, dummy_flag in enumerate(dummy_flags):
                conn.execute(
                    """
                    INSERT INTO player_secrets (secret_token, reward_points)
                    VALUES (?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 100 + i),
                )


def seed_sqli_adv_flag(conn):
    """Seed SQLI_ADV flag into isolated client_vault table."""
    if not PLAINTEXT_FLAGS:
        return
    sqli_adv_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "SQLI_ADV"), None)
    if sqli_adv_flag:
        _, code, _ = sqli_adv_flag
        with conn:
            # Clear and insert flag with dummy data
            conn.execute("DELETE FROM client_vault")
            conn.execute(
                """
                INSERT INTO client_vault (encrypted_data, access_level, metadata)
                VALUES (?, ?, ?)
                """,
                (encrypt_flag(code), 7, "classified"),
            )
            # Add realistic dummy flags to confuse students and automated tools
            dummy_flags = [
                "FLAG{Trust_me_its_ture_3}",
                "FLAG{Trust_me_its_false_3}",
                "FLAG{Not_the_real_flag_here}",
                "FLAG{Keep_looking_elsewhere}",
            ]
            for i, dummy_flag in enumerate(dummy_flags):
                conn.execute(
                    """
                    INSERT INTO client_vault (encrypted_data, access_level, metadata)
                    VALUES (?, ?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 5, "public"),
                )


def seed_sqli_blind_flag(conn):
    """Seed SQLI_BLIND flag into isolated access_keys table."""
    if not PLAINTEXT_FLAGS:
        return
    sqli_blind_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "SQLI_BLIND"), None)
    if sqli_blind_flag:
        _, code, _ = sqli_blind_flag
        with conn:
            # Clear and insert flag
            conn.execute("DELETE FROM access_keys")
            conn.execute(
                """
                INSERT INTO access_keys (auth_token, status_code)
                VALUES (?, ?)
                """,
                (encrypt_flag(code), 200),
            )
            # Add realistic dummy flags to confuse students and automated tools
            dummy_flags = [
                "FLAG{Trust_me_its_ture_4}",
                "FLAG{Trust_me_its_ture_5}",
                "FLAG{Trust_me_its_false_4}",
                "FLAG{Trust_me_its_false_5}",
                "FLAG{Wrong_flag_try_again}",
                "FLAG{This_wont_work_here}",
            ]
            for i, dummy_flag in enumerate(dummy_flags):
                conn.execute(
                    """
                    INSERT INTO access_keys (auth_token, status_code)
                    VALUES (?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 403),
                )


def seed_xss_flag(conn):
    """Seed XSS flag into isolated message_vault table."""
    if not PLAINTEXT_FLAGS:
        return
    xss_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "XSS"), None)
    if xss_flag:
        _, code, _ = xss_flag
        with conn:
            conn.execute("DELETE FROM message_vault")
            conn.execute(
                """
                INSERT INTO message_vault (hidden_content, priority_level, message_type)
                VALUES (?, ?, ?)
                """,
                (encrypt_flag(code), 9, "critical"),
            )
            # Add dummy flags
            dummy_flags = [
                "FLAG{Trust_me_its_ture_6}",
                "FLAG{Trust_me_its_false_6}",
                "FLAG{Not_the_xss_flag}",
            ]
            for dummy_flag in dummy_flags:
                conn.execute(
                    """
                    INSERT INTO message_vault (hidden_content, priority_level, message_type)
                    VALUES (?, ?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 5, "normal"),
                )


def seed_csrf_flag(conn):
    """Seed CSRF flag into isolated session_tokens table."""
    if not PLAINTEXT_FLAGS:
        return
    csrf_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "CSRF"), None)
    if csrf_flag:
        _, code, _ = csrf_flag
        with conn:
            conn.execute("DELETE FROM session_tokens")
            conn.execute(
                """
                INSERT INTO session_tokens (session_data, token_status, token_type)
                VALUES (?, ?, ?)
                """,
                (encrypt_flag(code), 1, "active"),
            )
            # Add dummy flags
            dummy_flags = [
                "FLAG{Trust_me_its_ture_7}",
                "FLAG{Trust_me_its_false_7}",
                "FLAG{Not_the_csrf_flag}",
            ]
            for dummy_flag in dummy_flags:
                conn.execute(
                    """
                    INSERT INTO session_tokens (session_data, token_status, token_type)
                    VALUES (?, ?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 0, "inactive"),
                )


def seed_steg_flag(conn):
    """Seed STEG flag into isolated image_metadata table."""
    if not PLAINTEXT_FLAGS:
        return
    steg_flag = next((f for f in PLAINTEXT_FLAGS if f[0] == "STEG"), None)
    if steg_flag:
        _, code, _ = steg_flag
        with conn:
            conn.execute("DELETE FROM image_metadata")
            conn.execute(
                """
                INSERT INTO image_metadata (embedded_data, image_type, metadata_info)
                VALUES (?, ?, ?)
                """,
                (encrypt_flag(code), 1, "hidden"),
            )
            # Add dummy flags
            dummy_flags = [
                "FLAG{Trust_me_its_ture_8}",
                "FLAG{Trust_me_its_false_8}",
                "FLAG{Not_the_steg_flag}",
            ]
            for dummy_flag in dummy_flags:
                conn.execute(
                    """
                    INSERT INTO image_metadata (embedded_data, image_type, metadata_info)
                    VALUES (?, ?, ?)
                    """,
                    (encrypt_flag(dummy_flag), 0, "visible"),
                )


def seed_leaderboard(conn):
    with conn:
        for roll_no, display_name, points in LEADERBOARD_PLAYERS:
            conn.execute(
                """
                INSERT INTO leaderboard (roll_no, display_name, points)
                VALUES (?, ?, ?)
                ON CONFLICT(roll_no) DO UPDATE SET
                    display_name=excluded.display_name,
                    points=excluded.points
                """,
                (roll_no, display_name, points),
            )


def seed_contracts(conn):
    with conn:
        for client_name, scope, budget, notes in CONTRACTS:
            conn.execute(
                """
                INSERT INTO contracts (client_name, scope, budget, confidential_notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(client_name) DO UPDATE SET
                    scope=excluded.scope,
                    budget=excluded.budget,
                    confidential_notes=excluded.confidential_notes
                """,
                (client_name, scope, budget, notes),
            )


def seed_shipments(conn):
    with conn:
        for tracking, destination, delivered in SHIPMENTS:
            conn.execute(
                """
                INSERT INTO shipments (tracking_number, destination, delivered)
                VALUES (?, ?, ?)
                ON CONFLICT(tracking_number) DO UPDATE SET
                    destination=excluded.destination,
                    delivered=excluded.delivered
                """,
                (tracking, destination, delivered),
            )


def seed_admins(conn):
    with conn:
        for username, password in ADMINS:
            conn.execute(
                """
                INSERT INTO admins (username, password_hash)
                VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash=excluded.password_hash
                """,
                (username, generate_password_hash(password)),
            )


def seed_students(conn, csv_path: Path):
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle, conn:
        reader = csv.DictReader(handle)
        required_columns = {"roll_no", "name", "password", "email"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")

        for row in reader:
            conn.execute(
                """
                INSERT INTO students (roll_no, name, email, password_hash)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(roll_no) DO UPDATE SET
                    name=excluded.name,
                    email=excluded.email,
                    password_hash=excluded.password_hash
                """,
                (
                    row["roll_no"].strip(),
                    row["name"].strip(),
                    row.get("email", "").strip(),
                    generate_password_hash(row["password"].strip()),
                ),
            )


def seed_student_stats(conn):
    with conn:
        conn.execute(
            """
            INSERT INTO student_stats (student_id, total_points, total_captures)
            SELECT students.id, 0, 0
            FROM students
            LEFT JOIN student_stats ss ON ss.student_id = students.id
            WHERE ss.student_id IS NULL
            """
        )


def add_demo_feedback(conn):
    existing = conn.execute("SELECT COUNT(*) AS total FROM feedback").fetchone()["total"]
    if existing:
        return

    cursor = conn.execute("SELECT id FROM students ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    if not row:
        return
    student_id = row["id"]
    sample_messages = [
        ("This board is perfect for testing stored XSS payloads. Try posting <script>alert('xss')</script>"),
        ("Remember: the teaching assistant account leaves hints here periodically."),
    ]
    with conn:
        for message in sample_messages:
            conn.execute(
                "INSERT INTO feedback (student_id, content, created_at) VALUES (?, ?, ?)",
                (student_id, message[0], datetime.utcnow().isoformat()),
            )


def main():
    parser = argparse.ArgumentParser(description="Initialize or update the vulnerable training database.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).parent / "data" / "students_sample.csv",
        help="Path to student roster CSV (columns: roll_no,name,password,email)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop the existing SQLite file before seeding (use cautiously; wipes progress).",
    )
    args = parser.parse_args()

    if args.reset:
        DB_PATH.unlink(missing_ok=True)
        print("Existing database removed.")

    conn = get_connection()
    bootstrap_schema(conn)
    seed_flags(conn)  # Empty now - all flags in isolated tables
    seed_sqli_basic_flag(conn)  # SQLI_BASIC into player_secrets
    seed_sqli_adv_flag(conn)  # SQLI_ADV into client_vault
    seed_sqli_blind_flag(conn)  # SQLI_BLIND into access_keys
    seed_xss_flag(conn)  # XSS into message_vault
    seed_csrf_flag(conn)  # CSRF into session_tokens
    seed_steg_flag(conn)  # STEG into image_metadata
    seed_leaderboard(conn)
    seed_contracts(conn)
    seed_shipments(conn)
    seed_admins(conn)
    seed_students(conn, args.csv)
    seed_student_stats(conn)
    add_demo_feedback(conn)
    conn.close()
    print(f"Database initialized/updated at {DB_PATH}")


if __name__ == "__main__":
    main()

