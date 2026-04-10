import datetime
import os
import sqlite3

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = os.getenv("SQLITE_PATH", "dollhouse.db")

USE_SQLITE = False

if DATABASE_URL:
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception:
        USE_SQLITE = True
        conn = sqlite3.connect(SQLITE_PATH)
else:
    USE_SQLITE = True
    conn = sqlite3.connect(SQLITE_PATH)

cur = conn.cursor()


def _normalize_query(query: str) -> str:
    if USE_SQLITE:
        return query.replace("%s", "?")
    return query


def _execute(query, params=()):
    cur.execute(_normalize_query(query), params)


# 💖 CREATE TABLES
cur.execute(
    """
_execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    xp INT DEFAULT 0,
    level INT DEFAULT 0,
    rep INT DEFAULT 0,
    coins INT DEFAULT 0,
    mood TEXT DEFAULT 'neutral'
)
"""
)

cur.execute(
    """
_execute("""
CREATE TABLE IF NOT EXISTS daily_rewards (
    user_id TEXT PRIMARY KEY,
    last_claim TIMESTAMP
)
"""
)

cur.execute(
    """
CREATE TABLE IF NOT EXISTS personalities (
    guild_id TEXT PRIMARY KEY,
    mode TEXT DEFAULT 'soft'
)
"""
)

cur.execute(
    """
CREATE TABLE IF NOT EXISTS vip_users (
    user_id TEXT PRIMARY KEY
)
"""
)

conn.commit()


# 💎 USER SYSTEM
def get_user(user_id):
    _execute("SELECT * FROM users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone()


def add_user(user_id, name="Unknown"):
    if not get_user(user_id):
        _execute(
            "INSERT INTO users (user_id, name) VALUES (%s, %s)",
            (str(user_id), name),
        )
        conn.commit()


def ensure_user(user_id, name="Unknown"):
    add_user(user_id, name)
    cur.execute("UPDATE users SET name=%s WHERE user_id=%s", (name, str(user_id)))
    conn.commit()


# 💎 XP + REP SYSTEM

def add_xp(user_id, amount):
    add_user(user_id)
    cur.execute(
# 💎 XP SYSTEM
def add_xp(user_id, amount):
    add_user(user_id)
    _execute(
        "UPDATE users SET xp = xp + %s WHERE user_id=%s",
        (amount, str(user_id)),
    )
    conn.commit()


def get_xp(user_id):
    add_user(user_id)
    cur.execute("SELECT xp FROM users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone()[0]


def add_rep(user_id, amount=1):
    add_user(user_id)
    cur.execute(
        "UPDATE users SET rep = rep + %s WHERE user_id=%s",
        (amount, str(user_id)),
    )
    conn.commit()


def get_rep(user_id):
    add_user(user_id)
    cur.execute("SELECT rep FROM users WHERE user_id=%s", (str(user_id),))
    _execute(
        "SELECT xp FROM users WHERE user_id=%s",
        (str(user_id),)
    )
    return cur.fetchone()[0]


def set_level(user_id, level):
    add_user(user_id)
    cur.execute("UPDATE users SET level=%s WHERE user_id=%s", (level, str(user_id)))
    conn.commit()


def check_level_up(user_id):
    xp = get_xp(user_id)
    level = xp // 50

    cur.execute("SELECT level FROM users WHERE user_id=%s", (str(user_id),))
    current = cur.fetchone()[0]

    if level > current:
        set_level(user_id, level)
    _execute(
        "SELECT level FROM users WHERE user_id=%s",
        (str(user_id),)
    )
    current = cur.fetchone()[0]

    if level > current:
        _execute(
            "UPDATE users SET level=%s WHERE user_id=%s",
            (level, str(user_id))
        )
        conn.commit()
        return level

    return None


# 💖 PERSONALITY MODE

def set_personality(guild_id, mode):
    cur.execute(
        """
        INSERT INTO personalities (guild_id, mode)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET mode=EXCLUDED.mode
        """,
        (str(guild_id), mode),
    )
    conn.commit()


def get_personality(guild_id):
    cur.execute("SELECT mode FROM personalities WHERE guild_id=%s", (str(guild_id),))
    row = cur.fetchone()
    return row[0] if row else "soft"


# 💰 COINS SYSTEM

def get_coins(user_id):
    add_user(user_id)
    cur.execute("SELECT coins FROM users WHERE user_id=%s", (str(user_id),))
# 💰 COINS SYSTEM
def get_coins(user_id):
    add_user(user_id)
    _execute(
        "SELECT coins FROM users WHERE user_id=%s",
        (str(user_id),)
    )
    return cur.fetchone()[0]


def add_coins(user_id, amount):
    add_user(user_id)
    cur.execute(
    _execute(
        "UPDATE users SET coins = coins + %s WHERE user_id=%s",
        (amount, str(user_id)),
    )
    conn.commit()


def remove_coins(user_id, amount):
    add_user(user_id)
    cur.execute(
    _execute(
        "UPDATE users SET coins = coins - %s WHERE user_id=%s",
        (amount, str(user_id)),
    )
    conn.commit()


# 🎁 DAILY SYSTEM
def check_daily(user_id):
    cur.execute("SELECT last_claim FROM daily_rewards WHERE user_id=%s", (str(user_id),))
    _execute(
        "SELECT last_claim FROM daily_rewards WHERE user_id=%s",
        (str(user_id),)
    )
    data = cur.fetchone()

    if not data:
        return False

    last_claim = data[0]
    if isinstance(last_claim, str):
        try:
            last_claim = datetime.datetime.fromisoformat(last_claim)
        except ValueError:
            return False

    now = datetime.datetime.utcnow()
    return (now - last_claim).total_seconds() < 86400


def give_daily(user_id, xp, coins):
    add_user(user_id)
    now = datetime.datetime.utcnow().isoformat()

    cur.execute(
        """
    _execute("""
    INSERT INTO daily_rewards (user_id, last_claim)
    VALUES (%s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET last_claim=%s
    """,
        (str(user_id), now, now),
    )

    _execute(
        "UPDATE users SET xp=xp+%s, coins=coins+%s WHERE user_id=%s",
        (xp, coins, str(user_id)),
    )
    conn.commit()


# 👑 VIP SYSTEM

def add_vip(user_id):
    cur.execute("INSERT INTO vip_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (str(user_id),))
    conn.commit()


def is_vip(user_id):
    cur.execute("SELECT 1 FROM vip_users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone() is not None


# 🏆 LEADERBOARDS
def get_top_coins():
    cur.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
    _execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
    return cur.fetchall()


def get_top_xp():
    cur.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10")
    _execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10")
    return cur.fetchall()
