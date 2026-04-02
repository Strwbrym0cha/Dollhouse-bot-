import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import random, asyncio, datetime, os
from zoneinfo import ZoneInfo
import psycopg2

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# 💎 DATABASE
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    rep INT DEFAULT 0,
    mood TEXT DEFAULT 'neutral',
    xp INT DEFAULT 0,
    level INT DEFAULT 0
)
""")

# VIP
cur.execute("""
CREATE TABLE IF NOT EXISTS vip_users (
    user_id TEXT PRIMARY KEY
)
""")

# VIP TIERS
cur.execute("""
CREATE TABLE IF NOT EXISTS vip_tiers (
    user_id TEXT PRIMARY KEY,
    tier TEXT
)
""")

# DAILY
cur.execute("""
CREATE TABLE IF NOT EXISTS daily_rewards (
    user_id TEXT PRIMARY KEY,
    last_claim TIMESTAMP
)
""")

# TICKETS
cur.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    channel_id TEXT,
    status TEXT DEFAULT 'open'
)
""")

conn.commit()

# 💖 BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

PINK = discord.Color.from_rgb(255,182,193)

def doll_embed(t,d):
    e = discord.Embed(title=t, description=d, color=PINK)
    e.set_footer(text="💖 Dollhouse • stay soft & powerful")
    return e

# 📍 IDS
WELCOME=1487458364593017064
EVENT=1487481426705256661
LEVEL_CH=1487467727722643527
COUNT_CH=1489330043510460547

VERIFY_ROLE="Verified Doll"
UNVERIFIED_ROLE="Unverified"

LEVEL_ROLES={
1:"porcelain doll",
5:"ribbon doll",
10:"velvet doll",
15:"lace doll",
20:"star doll",
30:"royal doll",
40:"diamond doll"
}

count=0
last=None

# 💖 READY
@bot.event
async def on_ready():
    print(f"{bot.user} online 💖")
    auto.start()
    weekly.start()

# 🔐 JOIN
@bot.event
async def on_member_join(m):
    r=discord.utils.get(m.guild.roles,name=UNVERIFIED_ROLE)
    if r: await m.add_roles(r)

# 💬 CORE SYSTEM
@bot.event
async def on_message(m):
    global count,last

    if m.author.bot:
        return

    uid=str(m.author.id)
    name=m.author.display_name

    # create/update user
    cur.execute("SELECT * FROM users WHERE user_id=%s",(uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id,name) VALUES (%s,%s)",(uid,name))
    else:
        cur.execute("UPDATE users SET name=%s WHERE user_id=%s",(name,uid))
    conn.commit()

    # counting
    if m.channel.id==COUNT_CH:
        if m.author==last:
            return await m.delete()
        try:
            n=int(m.content)
        except:
            return await m.delete()

        if n!=count+1:
            count=0
            return await m.channel.send("💔 reset")

        count=n
        last=m.author

    # XP
    gain=random.randint(5,10)

    cur.execute("SELECT * FROM vip_users WHERE user_id=%s",(uid,))
    if cur.fetchone():
        gain*=2

    cur.execute("UPDATE users SET xp=xp+%s WHERE user_id=%s RETURNING xp",(gain,uid))
    xp=cur.fetchone()[0]

    level=xp//50
    cur.execute("UPDATE users SET level=%s WHERE user_id=%s",(level,uid))
    conn.commit()

    # roles
    if level in LEVEL_ROLES:
        role=discord.utils.get(m.guild.roles,name=LEVEL_ROLES[level])
        if role and role not in m.author.roles:
            await m.author.add_roles(role)

    # rep
    cur.execute("UPDATE users SET rep=rep+1 WHERE user_id=%s",(uid,))
    conn.commit()

    # AI replies
    if "sad" in m.content.lower():
        await m.channel.send(f"🧸 {name} I got you 💖")
    if "lonely" in m.content.lower():
        await m.channel.send("💖 you're not alone here")

    await bot.process_commands(m)

# 🏆 COMMANDS

@bot.command()
async def profile(ctx):
    cur.execute("SELECT xp,level,rep FROM users WHERE user_id=%s",(str(ctx.author.id),))
    data=cur.fetchone()
    if not data:
        return await ctx.send("no data")

    xp,level,rep=data
    await ctx.send(embed=doll_embed("💖 Profile",f"Level: {level}\nXP: {xp}\nRep: {rep}"))

@bot.command()
async def leaderboard(ctx):
    cur.execute("SELECT user_id,xp FROM users ORDER BY xp DESC LIMIT 10")
    rows=cur.fetchall()

    text=""
    for i,(uid,xp) in enumerate(rows,1):
        m=ctx.guild.get_member(int(uid))
        if m:
            text+=f"{i}. {m.display_name} — {xp}\n"

    await ctx.send(embed=doll_embed("💎 Top Dolls",text))

@bot.command()
async def daily(ctx):
    uid=str(ctx.author.id)
    now=datetime.datetime.utcnow()

    cur.execute("SELECT last_claim FROM daily_rewards WHERE user_id=%s",(uid,))
    data=cur.fetchone()

    if data:
        if (now-data[0]).total_seconds()<86400:
            return await ctx.send("💖 come back later")

    cur.execute(
        "INSERT INTO daily_rewards (user_id,last_claim) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET last_claim=%s",
        (uid,now,now)
    )

    cur.execute("UPDATE users SET xp=xp+50 WHERE user_id=%s",(uid,))
    conn.commit()

    await ctx.send("🎁 +50 XP")

@bot.command()
@commands.has_permissions(administrator=True)
async def settier(ctx,user:discord.Member,tier:str):
    cur.execute(
        "INSERT INTO vip_tiers (user_id,tier) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET tier=%s",
        (str(user.id),tier,tier)
    )
    conn.commit()
    await ctx.send(f"{user.mention} is {tier}")

@bot.command()
@commands.has_permissions(administrator=True)
async def addvip(ctx,user:discord.Member):
    cur.execute("INSERT INTO vip_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",(str(user.id),))
    conn.commit()
    await ctx.send(f"{user.mention} VIP 💎")

@bot.command()
async def ticket(ctx):
    cat=discord.utils.get(ctx.guild.categories,name="tickets")
    if not cat:
        cat=await ctx.guild.create_category("tickets")

    ch=await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}",category=cat)
    await ch.set_permissions(ctx.author,read_messages=True,send_messages=True)

    cur.execute(
        "INSERT INTO tickets (user_id,channel_id) VALUES (%s,%s)",
        (str(ctx.author.id),str(ch.id))
    )
    conn.commit()

    await ch.send(f"{ctx.author.mention} support is here 💖")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx,amount:int):
    await ctx.channel.purge(limit=amount)

# 🎀 AUTO
@tasks.loop(hours=1)
async def auto():
    if bot.guilds:
        ch=bot.guilds[0].get_channel(WELCOME)
        if datetime.datetime.now().hour==10 and ch:
            await ch.send("🌸 good morning dolls 💖")

# 🎮 EVENTS
@tasks.loop(minutes=1)
async def weekly():
    if not bot.guilds:
        return
    now=datetime.datetime.now(ZoneInfo("America/Chicago"))
    g=bot.guilds[0]

    if now.weekday()==5 and now.hour==19:
        await g.get_channel(EVENT).send("🎮 game night 💖")

    if now.weekday()==6 and now.hour==18:
        await g.get_channel(EVENT).send("☕ tea time 💖")

bot.run(TOKEN)
