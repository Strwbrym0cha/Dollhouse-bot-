import datetime
import os
import sqlite3

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = os.getenv("SQLITE_PATH", "dollhouse.db")
USE_SQLITE = False

try:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        raise RuntimeError("DATABASE_URL not set")
except Exception:
    USE_SQLITE = True
    conn = sqlite3.connect(SQLITE_PATH)

cur = conn.cursor()


def _normalize_query(query: str) -> str:
    if USE_SQLITE:
        return query.replace("%s", "?")
    return query


def _execute(query: str, params=()):
    cur.execute(_normalize_query(query), params)


def _now_iso():
    return datetime.datetime.utcnow().isoformat()


_execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    rep INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    mood TEXT DEFAULT 'neutral'
)
""")

_execute("""
CREATE TABLE IF NOT EXISTS daily_rewards (
    user_id TEXT PRIMARY KEY,
    last_claim TEXT
)
""")

_execute("""
CREATE TABLE IF NOT EXISTS personalities (
    guild_id TEXT PRIMARY KEY,
    mode TEXT DEFAULT 'soft'
)
""")

_execute("""
CREATE TABLE IF NOT EXISTS vip_users (
    user_id TEXT PRIMARY KEY
)
""")

_execute("""
CREATE TABLE IF NOT EXISTS schedule_channels (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL
)
""")

_execute("""
CREATE TABLE IF NOT EXISTS schedule_sends (
    guild_id TEXT,
    event_date TEXT,
    event_name TEXT,
    PRIMARY KEY (guild_id, event_date, event_name)
)
""")

conn.commit()


def get_user(user_id):
    _execute("SELECT user_id, name, xp, level, rep, coins, mood FROM users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone()


def add_user(user_id, name="Unknown"):
    _execute(
        "INSERT INTO users (user_id, name) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
        (str(user_id), name),
    )
    conn.commit()


def ensure_user(user_id, name="Unknown"):
    add_user(user_id, name)
    _execute("UPDATE users SET name=%s WHERE user_id=%s", (name, str(user_id)))
    conn.commit()


def add_xp(user_id, amount):
    add_user(user_id)
    _execute("UPDATE users SET xp = xp + %s WHERE user_id=%s", (int(amount), str(user_id)))
    conn.commit()


def get_xp(user_id):
    add_user(user_id)
    _execute("SELECT xp FROM users WHERE user_id=%s", (str(user_id),))
    row = cur.fetchone()
    return row[0] if row else 0


def add_rep(user_id, amount=1):
    add_user(user_id)
    _execute("UPDATE users SET rep = rep + %s WHERE user_id=%s", (int(amount), str(user_id)))
    conn.commit()


def get_rep(user_id):
    add_user(user_id)
    _execute("SELECT rep FROM users WHERE user_id=%s", (str(user_id),))
    row = cur.fetchone()
    return row[0] if row else 0


def set_level(user_id, level):
    add_user(user_id)
    _execute("UPDATE users SET level=%s WHERE user_id=%s", (int(level), str(user_id)))
    conn.commit()


def check_level_up(user_id):
    add_user(user_id)
    xp = get_xp(user_id)
    new_level = xp // 50

    _execute("SELECT level FROM users WHERE user_id=%s", (str(user_id),))
    row = cur.fetchone()
    current_level = row[0] if row else 0

    if new_level > current_level:
        set_level(user_id, new_level)
        return new_level

    return None


def set_personality(guild_id, mode):
    _execute(
        """
        INSERT INTO personalities (guild_id, mode)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET mode=excluded.mode
        """,
        (str(guild_id), mode),
    )
    conn.commit()


def get_personality(guild_id):
    _execute("SELECT mode FROM personalities WHERE guild_id=%s", (str(guild_id),))
    row = cur.fetchone()
    return row[0] if row else "soft"


def get_coins(user_id):
    add_user(user_id)
    _execute("SELECT coins FROM users WHERE user_id=%s", (str(user_id),))
    row = cur.fetchone()
    return row[0] if row else 0


def add_coins(user_id, amount):
    add_user(user_id)
    _execute("UPDATE users SET coins = coins + %s WHERE user_id=%s", (int(amount), str(user_id)))
    conn.commit()


def remove_coins(user_id, amount):
    add_user(user_id)
    _execute("UPDATE users SET coins = coins - %s WHERE user_id=%s", (int(amount), str(user_id)))
    conn.commit()


def set_coins(user_id, amount):
    add_user(user_id)
    _execute("UPDATE users SET coins = %s WHERE user_id=%s", (max(int(amount), 0), str(user_id)))
    conn.commit()


def reset_user(user_id):
    add_user(user_id)
    _execute(
        "UPDATE users SET xp=0, level=0, rep=0, coins=0, mood='neutral' WHERE user_id=%s",
        (str(user_id),),
    )
    _execute("DELETE FROM daily_rewards WHERE user_id=%s", (str(user_id),))
    _execute("DELETE FROM vip_users WHERE user_id=%s", (str(user_id),))
    conn.commit()


def check_daily(user_id):
    _execute("SELECT last_claim FROM daily_rewards WHERE user_id=%s", (str(user_id),))
    row = cur.fetchone()
    if not row:
        return False

    try:
        last_claim = datetime.datetime.fromisoformat(str(row[0]))
    except ValueError:
        return False

    return (datetime.datetime.utcnow() - last_claim).total_seconds() < 86400


def give_daily(user_id, xp, coins):
    add_user(user_id)
    now = _now_iso()
    _execute(
        """
        INSERT INTO daily_rewards (user_id, last_claim)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET last_claim=excluded.last_claim
        """,
        (str(user_id), now),
    )
    _execute(
        "UPDATE users SET xp=xp+%s, coins=coins+%s WHERE user_id=%s",
        (int(xp), int(coins), str(user_id)),
    )
    conn.commit()


def add_vip(user_id):
    _execute("INSERT INTO vip_users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (str(user_id),))
    conn.commit()


def is_vip(user_id):
    _execute("SELECT 1 FROM vip_users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone() is not None


def set_schedule_channel(guild_id, channel_id):
    _execute(
        """
        INSERT INTO schedule_channels (guild_id, channel_id)
        VALUES (%s, %s)
        ON CONFLICT (guild_id) DO UPDATE SET channel_id=excluded.channel_id
        """,
        (str(guild_id), str(channel_id)),
    )
    conn.commit()


def get_schedule_channel(guild_id):
    _execute("SELECT channel_id FROM schedule_channels WHERE guild_id=%s", (str(guild_id),))
    row = cur.fetchone()
    return int(row[0]) if row else None


def get_schedule_channels():
    _execute("SELECT guild_id, channel_id FROM schedule_channels")
    return [(int(guild_id), int(channel_id)) for guild_id, channel_id in cur.fetchall()]


def schedule_message_sent(guild_id, event_date, event_name):
    _execute(
        "SELECT 1 FROM schedule_sends WHERE guild_id=%s AND event_date=%s AND event_name=%s",
        (str(guild_id), str(event_date), event_name),
    )
    return cur.fetchone() is not None


def mark_schedule_message_sent(guild_id, event_date, event_name):
    _execute(
        """
        INSERT INTO schedule_sends (guild_id, event_date, event_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (guild_id, event_date, event_name) DO NOTHING
        """,
        (str(guild_id), str(event_date), event_name),
    )
    conn.commit()


def get_top_coins():
    _execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
    return cur.fetchall()


def get_top_xp():
    _execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10")
    return cur.fetchall()
