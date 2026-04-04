import psycopg2
import os
import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 💖 CREATE TABLES
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    xp INT DEFAULT 0,
    level INT DEFAULT 0,
    rep INT DEFAULT 0,
    coins INT DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS daily_rewards (
    user_id TEXT PRIMARY KEY,
    last_claim TIMESTAMP
)
""")

conn.commit()


# 💎 USER SYSTEM

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=%s", (str(user_id),))
    return cur.fetchone()


def add_user(user_id, name="Unknown"):
    if not get_user(user_id):
        cur.execute(
            "INSERT INTO users (user_id, name) VALUES (%s, %s)",
            (str(user_id), name)
        )
        conn.commit()


# 💎 XP SYSTEM

def add_xp(user_id, amount):
    add_user(user_id)

    cur.execute(
        "UPDATE users SET xp = xp + %s WHERE user_id=%s",
        (amount, str(user_id))
    )

    conn.commit()


def get_xp(user_id):
    add_user(user_id)

    cur.execute(
        "SELECT xp FROM users WHERE user_id=%s",
        (str(user_id),)
    )

    return cur.fetchone()[0]


def check_level_up(user_id):
    xp = get_xp(user_id)
    level = xp // 50

    cur.execute(
        "SELECT level FROM users WHERE user_id=%s",
        (str(user_id),)
    )

    current = cur.fetchone()[0]

    if level > current:
        cur.execute(
            "UPDATE users SET level=%s WHERE user_id=%s",
            (level, str(user_id))
        )
        conn.commit()
        return level

    return None


# 💰 COINS SYSTEM

def get_coins(user_id):
    add_user(user_id)

    cur.execute(
        "SELECT coins FROM users WHERE user_id=%s",
        (str(user_id),)
    )

    return cur.fetchone()[0]


def add_coins(user_id, amount):
    add_user(user_id)

    cur.execute(
        "UPDATE users SET coins = coins + %s WHERE user_id=%s",
        (amount, str(user_id))
    )

    conn.commit()


def remove_coins(user_id, amount):
    add_user(user_id)

    cur.execute(
        "UPDATE users SET coins = coins - %s WHERE user_id=%s",
        (amount, str(user_id))
    )

    conn.commit()


# 🎁 DAILY SYSTEM

def check_daily(user_id):
    cur.execute(
        "SELECT last_claim FROM daily_rewards WHERE user_id=%s",
        (str(user_id),)
    )

    data = cur.fetchone()

    if not data:
        return False

    last_claim = data[0]
    now = datetime.datetime.utcnow()

    return (now - last_claim).total_seconds() < 86400


def give_daily(user_id, xp, coins):
    now = datetime.datetime.utcnow()

    cur.execute("""
    INSERT INTO daily_rewards (user_id, last_claim)
    VALUES (%s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET last_claim=%s
    """, (str(user_id), now, now))

    cur.execute(
        "UPDATE users SET xp=xp+%s, coins=coins+%s WHERE user_id=%s",
        (xp, coins, str(user_id))
    )

    conn.commit()


# 🏆 LEADERBOARDS

def get_top_coins():
    cur.execute(
        "SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10"
    )
    return cur.fetchall()


def get_top_xp():
    cur.execute(
        "SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10"
    )
    return cur.fetchall()
