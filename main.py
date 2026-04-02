import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import random, asyncio, datetime, os, io
from zoneinfo import ZoneInfo
import psycopg2

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# 💎 DATABASE
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS personalities (
    guild_id TEXT PRIMARY KEY,
    mode TEXT DEFAULT 'soft'
)
""")
conn.commit()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
user_id TEXT PRIMARY KEY,
name TEXT,
rep INT DEFAULT 0,
mood TEXT DEFAULT 'neutral',
xp INT DEFAULT 0,
level INT DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS vip_users (
user_id TEXT PRIMARY KEY)""")

cur.execute("""CREATE TABLE IF NOT EXISTS tickets (
id SERIAL PRIMARY KEY,
user_id TEXT,
channel_id TEXT,
status TEXT DEFAULT 'open')""")

cur.execute("""CREATE TABLE IF NOT EXISTS daily_rewards (
user_id TEXT PRIMARY KEY,
last_claim TIMESTAMP)""")

conn.commit()

# 💖 BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

PINK = discord.Color.from_rgb(255,182,193)

def doll_embed(t,d):
    e=discord.Embed(title=t,description=d,color=PINK)
    e.set_footer(text="💖 Dollhouse • stay soft & powerful")
    return e

# 📍 IDS (keep yours)
WELCOME=1487458364593017064
EVENT=1487481426705256661
LEVEL_CH=1487467727722643527
COUNT_CH=1489330043510460547
FRONT_DOOR = 1487458289221636277
VERIFY_ROLE="Verified Doll"
UNVERIFIED_ROLE="Unverified"

LEVEL_ROLES={1:"porcelain doll",5:"ribbon doll",10:"velvet doll",15:"lace doll",20:"star doll",30:"royal doll",40:"diamond doll"}

count=0
last=None

# 💖 READY
@bot.event
async def on_ready():
    print(f"{bot.user} online 💖")

    bot.add_view(VerifyView())  # 💎 keeps button working after restart

    auto.start()
    weekly.start()
# 🔐 JOIN + FRONT DOOR
@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Unverified Doll")
    if role:
        await member.add_roles(role)
# 🔐 VERIFY BUTTON
class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # 💎 keeps button alive forever

    @discord.ui.button(label="Enter Dollhouse 💖", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        verified = discord.utils.get(guild.roles, name="Verified Doll")
        unverified = discord.utils.get(guild.roles, name="Unverified Doll")

        if verified:
            await user.add_roles(verified)

        if unverified and unverified in user.roles:
            await user.remove_roles(unverified)

        await interaction.response.send_message(
            "💖 welcome inside the dollhouse… stay pretty ✨",
            ephemeral=True
        )

        # 🎀 welcome message
        channel = guild.get_channel(WELCOME)
        if channel:
            await channel.send(
                embed=doll_embed(
                    "🎀 New Doll Entered",
                    f"{user.mention} just joined the dollhouse 💖"
                )
            )
        # 💬 optional welcome message
        channel = guild.get_channel(WELCOME)
        if channel:
            await channel.send(f"🎀 {user.mention} just entered the Dollhouse 💖")
class RoleView(discord.ui.View):
    @discord.ui.button(label="🎮 Game Night", style=discord.ButtonStyle.primary)
    async def game(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="🎮 Game Night Ping")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("added 💖", ephemeral=True)

    @discord.ui.button(label="☕ Tea Time", style=discord.ButtonStyle.secondary)
    async def tea(self, interaction, button):
        role = discord.utils.get(interaction.guild.roles, name="☕ Tea Time Ping")
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("added 💖", ephemeral=True)
@bot.command()
async def verify(ctx):
    await ctx.send(
        embed=doll_embed(
            "🔐 Dollhouse Entrance",
            "Click the button below to enter 💖\n\n✨ must be 18+"
        ),
        view=VerifyView()
    )
    
@bot.command()
@commands.has_permissions(administrator=True)
async def personality(ctx, mode: str):
    mode = mode.lower()

    if mode not in ["soft", "sassy", "sweet", "strict"]:
        return await ctx.send("💖 modes: soft, sassy, sweet, strict")

    cur.execute(
        "INSERT INTO personalities (guild_id, mode) VALUES (%s,%s) ON CONFLICT (guild_id) DO UPDATE SET mode=%s",
        (str(ctx.guild.id), mode, mode)
    )
    conn.commit()

    await ctx.send(f"🎀 personality set to **{mode}** 💖")    
@bot.command()
async def menu(ctx):
    await ctx.send(embed=doll_embed(
        "🎀 Dollhouse Menu",
        """
💖 **Doll Commands**
!doll — affirmation  
!selfcare — self care tip  
!vibe — aesthetic vibe  

💎 **Progress**
!profile — your stats  
!daily — daily reward  
!leaderboard — top dolls  

🎟️ **Support**
!ticketpanel — open ticket  

🎀 **Access**
!roles — pick roles  
!verifypanel — verify  

👩‍💻 **Staff**
!clear <amount> — delete messages  
!addvip @user — VIP  

✨ stay pretty & active 💖
"""
    ))
@bot.command()
async def roles(ctx):
    await ctx.send(embed=doll_embed("🎀 Pick Roles","choose below 💖"), view=RoleView())
@bot.command()
async def sendverify(ctx):
    await ctx.send(embed=doll_embed("🔐 Verify","click below 💖"),view=VerifyView())

# 🎟️ TICKETS
class Ticket(View):
    @discord.ui.button(label="Open Ticket 💌",style=discord.ButtonStyle.success)
    async def open(self,i,b):
        g=i.guild
        cat=discord.utils.get(g.categories,name="tickets") or await g.create_category("tickets")
        ch=await g.create_text_channel(f"ticket-{i.user.name}",category=cat)
        await ch.set_permissions(i.user,read_messages=True,send_messages=True)

        cur.execute("INSERT INTO tickets (user_id,channel_id) VALUES (%s,%s)",(str(i.user.id),str(ch.id)))
        conn.commit()

        await ch.send(f"{i.user.mention} staff will help 💖")

@bot.command()
async def ticketpanel(ctx):
    await ctx.send(embed=doll_embed("💌 Support","open ticket 💖"),view=Ticket())

@bot.command()
async def close(ctx):
    msgs=[]
    async for m in ctx.channel.history(limit=100):
        msgs.append(f"{m.author}: {m.content}")
    file=discord.File(io.StringIO("\n".join(msgs)),"transcript.txt")
    await ctx.send(file=file)
    await ctx.channel.delete()

# 💬 CORE SYSTEM
@bot.event
async def on_message(m):
    global count, last

    if m.author.bot:
        return

    uid = str(m.author.id)
    name = m.author.display_name

    # 💖 GET PERSONALITY
    cur.execute(
        "SELECT mode FROM personalities WHERE guild_id=%s",
        (str(m.guild.id),)
    )
    row = cur.fetchone()
    mode = row[0] if row else "soft"

    # 🧠 MEMORY
    cur.execute("SELECT * FROM users WHERE user_id=%s", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (user_id,name) VALUES (%s,%s)", (uid, name))
    else:
        cur.execute("UPDATE users SET name=%s WHERE user_id=%s", (name, uid))
    conn.commit()

    # 🔢 COUNTING
    if not m.content.startswith("!") and m.channel.id == COUNT_CH:
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

    # 💎 XP SYSTEM
    if not m.content.startswith("!"):
        gain = random.randint(5, 10)

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

        # 💖 REP
        cur.execute("UPDATE users SET rep=rep+1 WHERE user_id=%s", (uid,))
        conn.commit()

        # 🤖 PERSONALITY RESPONSES
        content = m.content.lower()

        if "sad" in content:
            if mode == "soft":
                await m.channel.send(f"🧸 {name} I’m here for you 💖")
            elif mode == "sassy":
                await m.channel.send("💅 stand up doll, you’re too pretty to be sad")
            elif mode == "sweet":
                await m.channel.send("💖 sending you hugs and love ✨")
            elif mode == "strict":
                await m.channel.send("⚖️ focus. you got this.")

        if "lonely" in content:
            if mode == "soft":
                await m.channel.send("💖 you’re not alone here")
            elif mode == "sassy":
                await m.channel.send("pls you have us, don’t be dramatic 💅")

    # ⚖️ SOFT MOD
    if m.content.isupper() and len(m.content) > 15:
        await m.delete()
        await m.channel.send("💖 keep it cute")

    # ✅ MUST BE LAST
    await bot.process_commands(m)

# 🏆 COMMANDS
@bot.command()
async def rulespanel(ctx):
    await ctx.send(embed=doll_embed(
        "💖 DOLLHOUSE RULES",
        """
🔞 **this is an 18+ server only**  
by staying, you confirm you are 18 or older  

━━━━━━━━━━━━━━━━━━━  

💖 **1. be kind, always**  
treat every doll with respect — no bullying or harassment  

💖 **2. no hate or discrimination**  
this is a safe and inclusive space for everyone  

💖 **3. keep it cute**  
light profanity is okay, but don’t use it to attack others  

💖 **4. no spam or unwanted promo**  
only promote in the correct channels  

💖 **5. nsfw stays in nsfw channels**  
must be verified to access  

💖 **6. listen to staff**  
our dollhouse team keeps everything safe and smooth  

━━━━━━━━━━━━━━━━━━━  

💖 click verify to enter below ✨
"""
    ))
@bot.command()
async def rulespanel(ctx):
    await ctx.send(
        embed=doll_embed(
            "💖 DOLLHOUSE RULES",
            "read & click below to enter 💖"
        ),
        view=VerifyView()
    )    
@bot.command()
async def currentpersonality(ctx):
    cur.execute("SELECT mode FROM personalities WHERE guild_id=%s",(str(ctx.guild.id),))
    row = cur.fetchone()
    mode = row[0] if row else "soft"

    await ctx.send(f"💖 current personality: **{mode}**")
@bot.command()
async def profile(ctx):
    cur.execute("SELECT xp,level,rep FROM users WHERE user_id=%s",(str(ctx.author.id),))
    d=cur.fetchone()
    if not d:
        return await ctx.send("no data")
    await ctx.send(embed=doll_embed("💖 Profile",f"Level {d[1]}\nXP {d[0]}\nRep {d[2]}"))

@bot.command()
async def leaderboard(ctx):
    cur.execute("SELECT user_id,xp FROM users ORDER BY xp DESC LIMIT 10")
    rows=cur.fetchall()
    txt=""
    for i,(uid,xp) in enumerate(rows,1):
        m=ctx.guild.get_member(int(uid))
        if m: txt+=f"{i}. {m.display_name} — {xp}\n"
    await ctx.send(embed=doll_embed("💎 Top Dolls",txt))

@bot.command()
async def daily(ctx):
    conn2=psycopg2.connect(DATABASE_URL)
    cur2=conn2.cursor()

    uid=str(ctx.author.id)
    now=datetime.datetime.utcnow()

    cur2.execute("SELECT last_claim FROM daily_rewards WHERE user_id=%s",(uid,))
    d=cur2.fetchone()

    if d and d[0] and (now-d[0]).total_seconds()<86400:
        return await ctx.send("💖 come back later")

    cur2.execute("INSERT INTO daily_rewards (user_id,last_claim) VALUES (%s,%s) ON CONFLICT (user_id) DO UPDATE SET last_claim=%s",(uid,now,now))
    cur2.execute("UPDATE users SET xp=xp+50 WHERE user_id=%s",(uid,))
    conn2.commit()

    await ctx.send("🎁 +50 XP 💖")
@bot.command()
async def doll(ctx):
    affirmations = [
        "💖 you are THAT doll. don’t forget it.",
        "✨ pretty, powerful, and unstoppable.",
        "💅 soft doesn’t mean weak.",
        "🎀 you deserve everything you dream of.",
        "💎 you’re the main character, always."
    ]

    await ctx.send(embed=doll_embed(
        "💖 Doll Affirmation",
        random.choice(affirmations)
    ))
@bot.command()
async def selfcare(ctx):
    tips = [
        "🛁 take a warm shower & reset your energy",
        "📵 log off for a bit — protect your peace",
        "💤 rest is productive too",
        "🕯️ light a candle & breathe",
        "🎧 listen to music and just exist"
    ]

    await ctx.send(embed=doll_embed(
        "🧸 Self Care Reminder",
        random.choice(tips)
    ))    
# 👩‍💻 STAFF PANEL
@bot.command()
@commands.has_permissions(administrator=True)
async def staffpanel(ctx):
    await ctx.send(embed=doll_embed("👩‍💻 Staff Panel","!clear !ban !mute"))

# 🧹 CLEAR
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx,amount:int):
    await ctx.channel.purge(limit=amount)

# 💎 VIP
@bot.command()
@commands.has_permissions(administrator=True)
async def addvip(ctx,user:discord.Member):
    cur.execute("INSERT INTO vip_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING",(str(user.id),))
    conn.commit()
    await ctx.send(f"{user.mention} VIP 💎")

# 📢 AUTO
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
