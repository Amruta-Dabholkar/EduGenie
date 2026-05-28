import os
import bcrypt
import mysql.connector
from mysql.connector import Error


def get_connection():
    """
    Create and return a MySQL connection using env variables.
    Supports Aiven MySQL which requires SSL.
    Set DB_SSL=true in your .env when using Aiven.
    """
    use_ssl = os.getenv("DB_SSL", "false").lower() == "true"
    ssl_ca  = os.getenv("DB_SSL_CA", "")        # path to Aiven CA cert (optional)

    config = dict(
        host     = os.getenv("DB_HOST",     "mysql-252ed608-amrutadabholkar9404-653c.j.aivencloud.com"),
        port     = int(os.getenv("DB_PORT", "12077")),
        database = os.getenv("DB_NAME",     "defaultdb"),
        user     = os.getenv("DB_USER",     "avnadmin"),
        password = os.getenv("DB_PASSWORD", "AVNS_-3vSppp1LeNQphfDVWU"),
    )

    if use_ssl:
        if ssl_ca and os.path.exists(ssl_ca):
            # Use provided CA certificate (recommended for Aiven)
            config["ssl_ca"]       = ssl_ca
            config["ssl_verify_cert"] = True
        else:
            # Aiven enforces SSL but no local CA file — disable cert verification
            config["ssl_disabled"] = False
            config["ssl_verify_cert"] = False
            config["ssl_verify_identity"] = False

    return mysql.connector.connect(**config)


def init_db():
    """
    Create required tables if they don't exist.
    Call this once on app startup.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id    INT AUTO_INCREMENT PRIMARY KEY,
            username   VARCHAR(100) UNIQUE NOT NULL,
            password   VARCHAR(255) NOT NULL,
            role       ENUM('student', 'teacher') DEFAULT 'student',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            score_id   INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            pdf_name   VARCHAR(255),
            score      INT DEFAULT 0,
            total      INT DEFAULT 0,
            percentage FLOAT DEFAULT 0.0,
            taken_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# ──────────────────────────────────────────────
# USER AUTH
# ──────────────────────────────────────────────

def get_user(username: str, password: str) -> dict | None:
    """
    Verify credentials and return user dict if valid, else None.
    Returns: { user_id, username, role }
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, password, role FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            return {
                "user_id":  user["user_id"],
                "username": user["username"],
                "role":     user["role"],
            }
        return None

    except Error as e:
        print(f"[DB] get_user error: {e}")
        return None


def register_user(username: str, password: str, role: str = "student") -> bool:
    """
    Register a new user. Returns True on success, False if username exists.
    """
    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed, role)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True

    except mysql.connector.IntegrityError:
        # Username already exists
        return False
    except Error as e:
        print(f"[DB] register_user error: {e}")
        return False


# ──────────────────────────────────────────────
# QUIZ SCORES
# ──────────────────────────────────────────────

def save_score(user_id: int, pdf_name: str, score: int, total: int) -> bool:
    """Save a quiz result for a user."""
    try:
        percentage = round((score / total) * 100, 2) if total > 0 else 0.0

        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO quiz_scores (user_id, pdf_name, score, total, percentage)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, pdf_name, score, total, percentage)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"[DB] save_score error: {e}")
        return False


def get_scores(user_id: int) -> list:
    """
    Fetch all quiz scores for a user, most recent first.
    Returns list of dicts: { pdf_name, score, total, percentage, taken_at }
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT pdf_name, score, total, percentage,
                      DATE_FORMAT(taken_at, '%d %b %Y %H:%i') AS taken_at
               FROM quiz_scores
               WHERE user_id = %s
               ORDER BY taken_at DESC
               LIMIT 50""",
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    except Error as e:
        print(f"[DB] get_scores error: {e}")
        return []
