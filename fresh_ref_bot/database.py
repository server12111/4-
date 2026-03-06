import sqlite3
from config import DB_NAME


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                referrer_id INTEGER,
                balance REAL DEFAULT 0,
                total_earned REAL DEFAULT 0,
                ref_income REAL DEFAULT 0,
                tasks_done INTEGER DEFAULT 0,
                banned INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 1,
                join_date TEXT,
                last_login TEXT,
                last_bonus_date TEXT DEFAULT '',
                referral_reward_pending INTEGER DEFAULT 0,
                withdraw_count INTEGER DEFAULT 0,
                withdraw_total REAL DEFAULT 0,
                achievements TEXT DEFAULT 'Нет',
                used_free_promo INTEGER DEFAULT 0,
                last_spin_date TEXT DEFAULT '',
                daily_record INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                join_ts INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                reward REAL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS completed_tasks (
                user_id INTEGER,
                task_id INTEGER,
                PRIMARY KEY(user_id, task_id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                reward REAL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS used_promos (
                user_id INTEGER,
                code TEXT,
                PRIMARY KEY(user_id, code)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS withdraw_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                amount REAL,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                processed_at TEXT
            )
        ''')
        conn.execute('CREATE TABLE IF NOT EXISTS required_channels (link TEXT PRIMARY KEY)')
        conn.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
        conn.execute("INSERT OR IGNORE INTO config(key, value) VALUES ('bonus_min', '0.20')")
        conn.execute("INSERT OR IGNORE INTO config(key, value) VALUES ('bonus_max', '1.20')")
        conn.execute("INSERT OR IGNORE INTO config(key, value) VALUES ('log_chat_id', '0')")
        conn.execute("INSERT OR IGNORE INTO config(key, value) VALUES ('botohub_sponsors_count', '0')")
        conn.commit()
        # migrations for existing DBs
        for col, definition in [
            ('referral_reward_pending', 'INTEGER DEFAULT 0'),
            ('withdraw_count', 'INTEGER DEFAULT 0'),
            ('withdraw_total', 'REAL DEFAULT 0'),
            ('achievements', "TEXT DEFAULT 'Нет'"),
            ('used_free_promo', 'INTEGER DEFAULT 0'),
            ('last_spin_date', "TEXT DEFAULT ''"),
            ('daily_record', 'INTEGER DEFAULT 0'),
        ]:
            try:
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')
                conn.commit()
            except Exception:
                pass


def get_user(user_id: int):
    with get_db() as conn:
        return conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()


def refs_count(user_id: int) -> int:
    with get_db() as conn:
        return conn.execute(
            'SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,)
        ).fetchone()[0]


def today_refs_count(user_id: int) -> int:
    from datetime import datetime
    start_of_day = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    with get_db() as conn:
        return conn.execute(
            'SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND join_ts >= ?',
            (user_id, start_of_day),
        ).fetchone()[0]


def get_rank(refs: int) -> str:
    if refs >= 250: return 'Вне рангов 👑'
    if refs >= 200: return 'Легенда 🐉'
    if refs >= 150: return 'Профи 💎'
    if refs >= 100: return 'Опытный 🥇'
    if refs >= 75:  return 'Бывалый 🥈'
    if refs >= 50:  return 'Новичок 🥉'
    return 'Нет ранга ⚪'
