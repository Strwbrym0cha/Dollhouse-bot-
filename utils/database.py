import sqlite3

# connect to database (creates file automatically)
conn = sqlite3.connect("dollhouse.db")
cur = conn.cursor()

# create table
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    rep INTEGER DEFAULT 0
)
""")

conn.commit()


# 💎 GET USER
def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),))
    return cur.fetchone()


# 💎 ADD USER IF NOT EXISTS
def add_user(user_id):
    if not get_user(user_id):
        cur.execute(
            "INSERT INTO users (user_id, xp, level, rep) VALUES (?, 0, 0, 0)",
            (str(user_id),)
        )
        conn.commit()


# 💎 ADD XP
def add_xp(user_id, amount):
    add_user(user_id)

    cur.execute(
        "UPDATE users SET xp = xp + ? WHERE user_id = ?",
        (amount, str(user_id))
    )

    conn.commit()


# 💎 GET XP
def get_xp(user_id):
    add_user(user_id)

    cur.execute(
        "SELECT xp FROM users WHERE user_id = ?",
        (str(user_id),)
    )

    return cur.fetchone()[0]


# 💎 ADD REP
def add_rep(user_id, amount):
    add_user(user_id)

    cur.execute(
        "UPDATE users SET rep = rep + ? WHERE user_id = ?",
        (amount, str(user_id))
    )
def check_level_up(user_id):
    xp = get_xp(user_id)
    level = xp // 100

    cur.execute("SELECT level FROM users WHERE user_id = ?", (str(user_id),))
    current_level = cur.fetchone()[0]

    if level > current_level:
        cur.execute(
            "UPDATE users SET level = ? WHERE user_id = ?",
            (level, str(user_id))
        )
        conn.commit()
        return level

    return None
    conn.commit()
