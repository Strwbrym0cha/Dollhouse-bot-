# 💖 IMPORTS
import discord
from discord.ext import commands, tasks
from discord.ui import View, Select
import random, datetime, os, io
from zoneinfo import ZoneInfo
import psycopg2

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# 💎 DATABASE
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
user_id TEXT PRIMARY KEY,
name TEXT,
rep INT DEFAULT 0,
xp INT DEFAULT 0,
level INT DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS vip_users (
user_id TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS tickets (
id SERIAL PRIMARY KEY,
user_id TEXT,
channel_id TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS warnings (
user_id TEXT,
count INT DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS personalities (
guild_id TEXT PRIMARY KEY,
mode TEXT DEFAULT 'soft'
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS daily_rewards (
user_id TEXT PRIMARY KEY,
last_claim TIMESTAMP
)""")
cur.execute("""
ALTER TABLE users
ADD COLUMN IF NOT EXISTS coins INT DEFAULT 0
""")
conn.commit()

# 💖 BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

PINK = discord.Color.from_rgb(255,182,193)

def doll_embed(t,d):
    e=discord.Embed(title=t,description=d,color=PINK)
    e.set_footer(text="💖 Dollhouse")
    return e

# 📍 IDS
WELCOME=1487458364593017064
EVENT=1487481426705256661
LEVEL_CH=1487467727722643527
COUNT_CH=1489330043510460547

LEVEL_ROLES={1:"🧸 Porcelain Doll",5:"🎀 Ribbon Doll",10:"💖 Velvet Doll",15:"🌸 Lace Doll",20:"✨ Star Doll",30:"👑 Royal Doll",40:"💎 Diamond Doll"}

count=0
last=None

# 🔐 VERIFY
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enter Dollhouse 💖",
        style=discord.ButtonStyle.success,
        custom_id="verify_button"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = interaction.guild
        u = interaction.user

        v = discord.utils.get(g.roles, name="Verified Doll")
        uv = discord.utils.get(g.roles, name="Unverified Doll")

        if v:
            await u.add_roles(v)
        if uv and uv in u.roles:
            await u.remove_roles(uv)

        await interaction.response.send_message("💖 welcome inside ✨", ephemeral=True)
# 🎀 ROLE SELECT
class RoleSelect(Select):
    def __init__(self, placeholder, roles, emojis):
        options = [
            discord.SelectOption(label=r, emoji=e)
            for r, e in zip(roles, emojis)
        ]

        super().__init__(
            placeholder=placeholder,
            options=options,
            custom_id=placeholder  # 💖 REQUIRED
        )

        self.role_names = roles

    async def callback(self, interaction):
        for role in interaction.guild.roles:
            if role.name in self.role_names:
                await interaction.user.remove_roles(role)

        role = discord.utils.get(interaction.guild.roles, name=self.values[0])
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("💖 updated!", ephemeral=True)

# 🎀 ROLE VIEWS
class AgeView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("Age 💖",["🔞 18–20","💖 21–25","👑 26+"],["🔞","💖","👑"]))

class GenderView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect("Gender 💅",["💖 Girl","💙 Boy","🌸 Non-binary","🖤 Prefer not"],["💖","💙","🌸","🖤"]))

class EventView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎮 Game Night",
        style=discord.ButtonStyle.primary,
        custom_id="game_ping"
    )
    async def game(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(
            interaction.guild.roles,
            name="🎮 Game Night Ping"
        )

        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            "🎮 you got the game night role 💖",
            ephemeral=True
        )
# 🎟️ TICKET
class Ticket(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Open Ticket 💌",
        style=discord.ButtonStyle.success,
        custom_id="ticket_open"
    )
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = interaction.guild

        cat = discord.utils.get(g.categories, name="tickets") or await g.create_category("tickets")

        ch = await g.create_text_channel(f"ticket-{interaction.user.name}", category=cat)

        await ch.set_permissions(interaction.user, read_messages=True, send_messages=True)

        cur.execute(
            "INSERT INTO tickets (user_id,channel_id) VALUES (%s,%s)",
            (str(interaction.user.id), str(ch.id))
        )
        conn.commit()

        await ch.send(f"{interaction.user.mention} support will help 💖")
# 💖 READY
@bot.event
async def on_ready():
    print("online 💖")

    try:
        bot.add_view(VerifyView())
        bot.add_view(AgeView())
        bot.add_view(GenderView())
        bot.add_view(EventView())
        bot.add_view(Ticket())

        if not doll_of_day.is_running():
            doll_of_day.start()

        if not auto.is_running():
            auto.start()

        if not weekly.is_running():
            weekly.start()

        if not check_unverified.is_running():
            check_unverified.start()

    except Exception as e:
        print("ERROR IN ON_READY:", e)
# 💬 MESSAGE SYSTEM
# 💖 FIXED CRITICAL SECTION (REPLACE YOUR on_message)

@bot.event
async def on_message(m):
    global count, last

    if m.author.bot:
        return

    uid = str(m.author.id)
    name = m.author.display_name

    # 🧠 CREATE USER
    cur.execute("SELECT * FROM users WHERE user_id=%s", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id,name) VALUES (%s,%s)", (uid, name))
        conn.commit()

    # 💰 COINS (FIXED)
    coins = random.randint(1, 5)
    cur.execute(
        "UPDATE users SET coins=coins+%s WHERE user_id=%s",
        (coins, uid)
    )

    # 🧠 MEMORY UPDATE
    cur.execute(
        "UPDATE users SET name=%s WHERE user_id=%s",
        (name, uid)
    )

    conn.commit()

    # 💎 XP SYSTEM
    if not m.content.startswith("!"):
        gain = random.randint(5, 10)

        # 👑 VIP BOOST
        cur.execute("SELECT * FROM vip_users WHERE user_id=%s", (uid,))
        if cur.fetchone():
            gain *= 2

        cur.execute(
            "UPDATE users SET xp=xp+%s WHERE user_id=%s RETURNING xp",
            (gain, uid)
        )
        xp = cur.fetchone()[0]

        level = xp // 50

        cur.execute(
            "UPDATE users SET level=%s WHERE user_id=%s",
            (level, uid)
        )
        conn.commit()

        # 🎀 LEVEL ROLES
        if level in LEVEL_ROLES:
            role = discord.utils.get(m.guild.roles, name=LEVEL_ROLES[level])
            if role and role not in m.author.roles:
                await m.author.add_roles(role)

                ch = m.guild.get_channel(LEVEL_CH)
                if ch:
                    await ch.send(
                        f"💖 {m.author.mention} reached {LEVEL_ROLES[level]} ✨"
                    )

    # 🔢 COUNTING SYSTEM (FIXED POSITION)
    if m.channel.id == COUNT_CH and not m.content.startswith("!"):
        if m.author == last:
            return await m.delete()

        try:
            n = int(m.content)
        except:
            return await m.delete()

        if n != count + 1:
            count = 0
            return await m.channel.send("💔 reset")

        count = n
        last = m.author

        if count == 50:
            role = discord.utils.get(m.guild.roles, name="🌟 Featured Doll")
            if role:
                await m.author.add_roles(role)
                await m.channel.send("🌟 milestone reached 💖")

    # 🤖 PERSONALITY (FIXED)
    content = m.content.lower()

    if "sad" in content:
        await m.channel.send(f"🧸 {name} I’m here for you 💖")

    if "lonely" in content:
        await m.channel.send("💖 you’re not alone here")

    # 💖 RANDOM BOOST MESSAGE
    if random.randint(1, 20) == 1:
        await m.channel.send("💖 you're doing amazing ✨")

    await bot.process_commands(m)
# 💎 COMMANDS
@bot.command()
@commands.has_permissions(administrator=True)
async def staffpanel(ctx):
    await ctx.send(embed=doll_embed("👩‍💻 Staff Panel","!clear !ban !mute"))

@bot.command()
async def currentpersonality(ctx):
    cur.execute("SELECT mode FROM personalities WHERE guild_id=%s",(str(ctx.guild.id),))
    row = cur.fetchone()
    mode = row[0] if row else "soft"

    await ctx.send(f"💖 current personality: **{mode}**")
@bot.command()
async def profile(ctx):
    cur.execute("SELECT xp,level,rep,coins FROM users WHERE user_id=%s",(str(ctx.author.id),))
    d = cur.fetchone()

    if not d:
        return await ctx.send("no data")

    await ctx.send(embed=doll_embed(
        "💖 Doll Profile",
        f"""
✨ Level: {d[1]}
💎 XP: {d[0]}
💖 Rep: {d[2]}
💰 Coins: {d[3]}
"""
    ))
@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    now = datetime.datetime.utcnow()

    cur.execute("SELECT last_claim FROM daily_rewards WHERE user_id=%s",(uid,))
    d = cur.fetchone()

    if d and d[0] and (now - d[0]).total_seconds() < 86400:
        return await ctx.send("💖 come back later")

    reward = random.randint(50, 100)

    cur.execute("""
    INSERT INTO daily_rewards (user_id,last_claim)
    VALUES (%s,%s)
    ON CONFLICT (user_id)
    DO UPDATE SET last_claim=%s
    """,(uid,now,now))

    cur.execute("UPDATE users SET xp=xp+%s, coins=coins+%s WHERE user_id=%s",(reward,reward//2,uid))
    conn.commit()

    await ctx.send(f"🎁 +{reward} XP & 💰 {reward//2} coins 💖")
@bot.command()
async def buy(ctx, item: str):
    uid = str(ctx.author.id)

    cur.execute("SELECT coins FROM users WHERE user_id=%s", (uid,))
    data = cur.fetchone()

    if not data:
        return await ctx.send("💖 no data")

    coins = data[0]

    if item == "vip" and coins >= 200:
        role = discord.utils.get(ctx.guild.roles, name="👑 VIP Doll")
        await ctx.author.add_roles(role)

        cur.execute("UPDATE users SET coins=coins-200 WHERE user_id=%s", (uid,))
        conn.commit()

        await ctx.send("👑 VIP unlocked 💎")

    else:
        await ctx.send("💔 not enough coins")
@bot.command()
async def shop(ctx):
    await ctx.send(embed=doll_embed(
        "🛍️ Dollhouse Shop",
        """
💎 100 coins — 🎀 Custom Role  
💎 200 coins — 💖 VIP (24h)  
💎 50 coins — 🌟 Featured Doll  
"""
    ))
@bot.command()
async def rolespanel(ctx):
    await ctx.send(embed=doll_embed("🔞 Age","💖"),view=AgeView())
    await ctx.send(embed=doll_embed("💅 Gender","💖"),view=GenderView())
    await ctx.send(embed=doll_embed("🎮 Events","💖"),view=EventView())

@bot.command()
async def ticketpanel(ctx):
    await ctx.send(embed=doll_embed("Support","💌"),view=Ticket())

@bot.command()
async def warn(ctx,member:discord.Member):
    cur.execute("INSERT INTO warnings (user_id,count) VALUES (%s,1)",(str(member.id),))
    conn.commit()
    await ctx.send(f"{member.mention} warned")

@bot.command()
async def leaderboard(ctx):
    cur.execute("SELECT user_id,xp FROM users ORDER BY xp DESC LIMIT 10")
    rows=cur.fetchall()
    txt=""
    for i,(uid,xp) in enumerate(rows,1):
        m=ctx.guild.get_member(int(uid))
        if m: txt+=f"{i}. {m.display_name} — {xp}\n"
    await ctx.send(embed=doll_embed("Leaderboard",txt))
# 💎 VIP
@bot.command()
@commands.has_permissions(administrator=True)
async def addvip(ctx, member: discord.Member):
    cur.execute(
        "INSERT INTO vip_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",
        (str(member.id),)
    )
    conn.commit()

    await ctx.send(f"{member.mention} is VIP 💎")
@bot.command()
@commands.has_permissions(administrator=True)
async def personality(ctx, mode: str):
    mode = mode.lower()

    if mode not in ["soft", "sassy", "sweet", "strict"]:
        await ctx.send(f"💖 personality set to {mode}")

    cur.execute(
        "INSERT INTO personalities (guild_id, mode) VALUES (%s,%s) ON CONFLICT (guild_id) DO UPDATE SET mode=%s",
        (str(ctx.guild.id), mode, mode)
    )
    conn.commit()
 
# 📢 AUTO
@tasks.loop(hours=1)
async def auto():
    if bot.guilds:
        ch=bot.guilds[0].get_channel(WELCOME)
        if ch and datetime.datetime.now().hour==10:
            await ch.send("🌸 good morning dolls 💖")
@tasks.loop(minutes=1)
async def check_unverified():
    for guild in bot.guilds:
        role = discord.utils.get(guild.roles, name="Unverified Doll")
        if not role:
            continue

        for member in guild.members:
            if role in member.roles:
                joined = member.joined_at

                if not joined:
                    continue

                now = datetime.datetime.now(datetime.UTC)
                diff = (now - joined).total_seconds()

                # 💖 10 MIN WARNING
                if 600 < diff < 660:
                    try:
                        await member.send(
                            "💖 hey doll! please verify in the server or you’ll be removed soon ✨"
                        )
                    except:
                        pass

                # 🚨 15 MIN FINAL
                if diff > 900:
                    try:
                        await member.send(
                            "💔 you weren’t verified in time, come back anytime 💖"
                        )
                    except:
                        pass

                    try:
                        await member.kick(reason="Not verified in time")
                    except:
                        pass
# 🎮 EVENTS
@tasks.loop(minutes=1)
async def weekly():
    if not bot.guilds:
        return

    now = datetime.datetime.now(ZoneInfo("America/Chicago"))
    g = bot.guilds[0]

    ch = g.get_channel(EVENT)

    if ch and now.weekday() == 5 and now.hour == 19:
        await ch.send("🎮 game night 💖")
@tasks.loop(hours=24)
async def doll_of_day():
    if not bot.guilds:
        return

    g = bot.guilds[0]
    ch = g.get_channel(WELCOME)

    members = [m for m in g.members if not m.bot]

    if members and ch:
        user = random.choice(members)
        await ch.send(f"🌟 Doll of the Day: {user.mention} 💖")
bot.run(TOKEN)
