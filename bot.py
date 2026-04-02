import os
import io
import random
import asyncio
import datetime
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from zoneinfo import ZoneInfo

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

PINK = discord.Color.from_rgb(255, 182, 193)

def doll_embed(title, description):
    e = discord.Embed(title=title, description=description, color=PINK)
    e.set_footer(text="💖 Dollhouse • stay soft & powerful")
    return e

# ── Channel & role IDs ────────────────────────────────────────────────────────
WELCOME      = 1487458364593017064
EVENT        = 1487481426705256661
GIVEAWAY     = 1487481479947616397
LEVEL_CH     = 1487467727722643527
COUNT_CH     = 1489330043510460547

VERIFY_ROLE   = "Verified Doll"
UNVERIFIED_ROLE = "Unverified"

LEVEL_ROLES = {
    1:  "porcelain doll",
    5:  "ribbon doll",
    10: "velvet doll",
    15: "lace doll",
    20: "star doll",
    30: "royal doll",
    40: "diamond doll",
}

def lvl(x):
    return x // 50

premium = set()

# Counting game state
count = 0
last  = None


# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def increment_rep(user_id: int) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE user_memory SET rep = rep + 1, updated_at = NOW()
        WHERE user_id = %s RETURNING rep
    """, (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row[0] if row else 0


def upsert_memory(user_id: int, guild_id: int, name: str) -> dict:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_memory (user_id, guild_id, name, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE
            SET name = EXCLUDED.name, updated_at = NOW()
        RETURNING user_id, name, rep, mood
    """, (user_id, guild_id, name))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {"user_id": row[0], "name": row[1], "rep": row[2], "mood": row[3]}


def get_xp_db(user_id: int) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT xp FROM user_xp WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else 0


def add_xp_db(user_id: int, guild_id: int, amount: int) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_xp (user_id, guild_id, xp, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE
            SET xp = user_xp.xp + EXCLUDED.xp,
                updated_at = NOW()
        RETURNING xp
    """, (user_id, guild_id, amount))
    xp = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return xp


def reset_all_xp():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE user_xp SET xp = 0")
    conn.commit()
    cur.close()
    conn.close()


def get_server_settings(guild_id: int) -> dict:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO server_settings (guild_id)
        VALUES (%s)
        ON CONFLICT (guild_id) DO NOTHING
    """, (guild_id,))
    conn.commit()
    cur.execute("""
        SELECT event_channel, welcome_channel, vip_role, verify_role, log_channel
        FROM server_settings WHERE guild_id = %s
    """, (guild_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "event_channel":   row[0],
        "welcome_channel": row[1],
        "vip_role":        row[2],
        "verify_role":     row[3],
        "log_channel":     row[4],
    }


def update_server_setting(guild_id: int, key: str, value: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"""
        INSERT INTO server_settings (guild_id, {key}, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (guild_id) DO UPDATE
            SET {key} = EXCLUDED.{key}, updated_at = NOW()
    """, (guild_id, value))
    conn.commit()
    cur.close()
    conn.close()


def get_leaderboard(guild_id: int, limit: int = 10):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, xp FROM user_xp
        WHERE guild_id = %s
        ORDER BY xp DESC
        LIMIT %s
    """, (guild_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def add_event_signup(user_id: int, guild_id: int, event_name: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO event_signups (user_id, guild_id, event_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, guild_id, event_name) DO NOTHING
        RETURNING id
    """, (user_id, guild_id, event_name))
    inserted = cur.fetchone() is not None
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def get_event_signups(guild_id: int, event_name: str) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM event_signups WHERE guild_id = %s AND event_name = %s",
        (guild_id, event_name)
    )
    c = cur.fetchone()[0]
    cur.close()
    conn.close()
    return c


# ── Views ─────────────────────────────────────────────────────────────────────

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify ✨", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        if not interaction.guild:
            return
        vr = discord.utils.get(interaction.guild.roles, name=VERIFY_ROLE)
        ur = discord.utils.get(interaction.guild.roles, name=UNVERIFIED_ROLE)
        if vr:
            member = await interaction.guild.fetch_member(interaction.user.id)
            await member.add_roles(vr)
            if ur:
                await member.remove_roles(ur)
            await interaction.response.send_message("💖 You are now verified! Welcome in ✨", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Verified Doll role not found. Contact an admin.", ephemeral=True)


class Ticket(View):
    @discord.ui.button(label="Open Ticket 💌", style=discord.ButtonStyle.success, custom_id="open_ticket")
    async def open(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        g = interaction.guild

        # Check if user already has an open ticket
        existing = discord.utils.get(g.text_channels, name=f"ticket-{interaction.user.name}")
        if existing:
            return await interaction.followup.send(
                f"💖 You already have an open ticket: {existing.mention}", ephemeral=True
            )

        # Get or create the tickets category
        cat = discord.utils.get(g.categories, name="tickets")
        if cat is None:
            cat = await g.create_category("tickets")

        try:
            # Hide from everyone by default
            overwrites = {
                g.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            # Give admins access too
            for role in g.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            ch = await g.create_text_channel(
                f"ticket-{interaction.user.name}",
                category=cat,
                overwrites=overwrites
            )
            await ch.send(
                embed=doll_embed("💌 New Ticket", f"{interaction.user.mention} staff will be with you shortly ✨\n\nUse `!close` to close this ticket.")
            )
            await interaction.followup.send(f"💖 Ticket created: {ch.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to create channels.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Something went wrong: {e}", ephemeral=True)


class EventView(View):
    def __init__(self, event_name: str = "Weekly Game Night"):
        super().__init__(timeout=None)
        self.event_name = event_name
        btn = Button(label="Join Event 💖", style=discord.ButtonStyle.success, custom_id="join_event")
        btn.callback = self.join_event
        self.add_item(btn)

    async def join_event(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else 0
        is_new   = add_event_signup(interaction.user.id, guild_id, self.event_name)
        total    = get_event_signups(guild_id, self.event_name)
        if is_new:
            await interaction.response.send_message(
                f"💖 You're signed up for **{self.event_name}**! ({total} signed up)", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"✨ Already signed up for **{self.event_name}**! ({total} total)", ephemeral=True)


# ── Scheduled tasks ───────────────────────────────────────────────────────────

@tasks.loop(hours=1)
async def auto():
    if not bot.guilds:
        return
    ch  = bot.guilds[0].get_channel(WELCOME)
    now = datetime.datetime.now()
    if now.hour == 10 and ch:
        await ch.send("🌸 good morning dolls 💖")


@tasks.loop(minutes=1)
async def weekly():
    if not bot.guilds:
        return
    now = datetime.datetime.now(ZoneInfo("America/Chicago"))
    g   = bot.guilds[0]
    e   = g.get_channel(EVENT)
    gch = g.get_channel(GIVEAWAY)

    if now.weekday() == 5 and now.hour == 19 and now.minute == 0:
        if e:
            await e.send("🎮 game night 💖")
    if now.weekday() == 5 and now.hour == 20 and now.minute == 0:
        if gch:
            msg = await gch.send("🎁 giveaway 🎉")
            await msg.add_reaction("🎉")
    if now.weekday() == 6 and now.hour == 18 and now.minute == 0:
        if e:
            await e.send("☕ tea time 💖")


@tasks.loop(hours=168)
async def weekly_rewards():
    reset_all_xp()


# ── Bot events ────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    save(memory, "memory.json")
    weekly.start()
    auto.start()
    weekly_rewards.start()


@bot.event
async def on_member_join(member):
    ur = discord.utils.get(member.guild.roles, name=UNVERIFIED_ROLE)
    if ur:
        await member.add_roles(ur)
    ch = member.guild.get_channel(WELCOME)
    if ch:
        await ch.send(embed=doll_embed("🎀 Welcome", f"{member.mention} verify 💖"))
    await asyncio.sleep(300)
    if ur in member.roles:
        await member.kick(reason="not verified")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.member is None or payload.member.bot:
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    role_map = {"🎮": "Gamer Doll", "🎨": "Artist Doll", "💬": "Chatty Doll"}
    role_name = role_map.get(payload.emoji.name)
    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await payload.member.add_roles(role)


@bot.event
async def on_message(message):
    global count, last
    if message.author.bot:
        return

    guild_id = message.guild.id if message.guild else 0
    upsert_memory(message.author.id, guild_id, message.author.display_name)

    # Counting game
    if message.guild and message.channel.id == COUNT_CH:
        if message.author == last:
            return await message.delete()
        try:
            n = int(message.content)
        except ValueError:
            return await message.delete()
        if n != count + 1:
            count = 0
            await message.channel.send("reset 💔")
            return
        count = n
        last  = message.author

        if count == 50:
            role = discord.utils.get(message.guild.roles, name="🌟 Featured Doll")
            if role:
                await message.author.add_roles(role)
                await message.channel.send(
                    embed=doll_embed("🌟 Featured Doll", f"{message.author.mention} hit 50 and earned the Featured Doll role 💖")
                )

    # XP (2x for premium)
    gain      = random.randint(5, 10)
    if message.author.id in premium:
        gain *= 2
    xp_total  = add_xp_db(message.author.id, guild_id, gain)
    level     = lvl(xp_total)

    # Level roles
    if message.guild and level in LEVEL_ROLES:
        new_role_name = LEVEL_ROLES[level]
        new_role      = discord.utils.get(message.guild.roles, name=new_role_name)
        if new_role and new_role not in message.author.roles:
            for r_name in LEVEL_ROLES.values():
                old = discord.utils.get(message.guild.roles, name=r_name)
                if old and old in message.author.roles:
                    await message.author.remove_roles(old)
            await message.author.add_roles(new_role)
            ch = message.guild.get_channel(LEVEL_CH)
            if ch:
                await ch.send(embed=doll_embed("💖 Glow Up", f"{message.author.mention} → {new_role_name}"))

    # Soft mod — no all-caps
    if message.content.isupper() and len(message.content) > 15:
        await message.delete()
        await message.channel.send(f"💖 {message.author.mention} keep it cute 🧸")

    # Vibe check
    if "sad" in message.content.lower():
        mem = upsert_memory(message.author.id, guild_id, message.author.display_name)
        await message.channel.send(f"🧸 {mem['name']} I got you 💖")

    # Rep increment
    increment_rep(message.author.id)

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print("ERROR:", error)
    try:
        await ctx.send(f"❌ {error}")
    except Exception:
        pass


# ── Commands ──────────────────────────────────────────────────────────────────

@bot.command()
async def hello(ctx):
    await ctx.send("✨ Bot is working!")


@bot.command()
async def affirm(ctx):
    affirmations = [
        "You are enough, always 💖",
        "You radiate soft power ✨",
        "You are doing so well, doll 🎀",
        "Your presence is a gift 💋",
        "You are worthy of every good thing 🌸",
        "You are beautiful inside and out 💅",
        "The world is better with you in it 🧸",
        "You are stronger than you know 💎",
    ]
    await ctx.send(embed=doll_embed("💖 Affirmation", random.choice(affirmations)))


@bot.command()
async def doll(ctx):
    responses = [
        "You're a doll 💖 never forget it ✨",
        "Serving looks and kindness 💅 that's the dollhouse way",
        "Soft but powerful 🎀 just like you",
        "A true doll knows her worth 💎",
        "Stay cute, stay powerful 🌸",
    ]
    await ctx.send(embed=doll_embed("🎀 Doll Check", random.choice(responses)))


@bot.command()
async def selfcare(ctx):
    tips = [
        "Drink some water 💧 you deserve it",
        "Take a deep breath 🌸 you're doing great",
        "Rest is productive too 🧸 don't forget to recharge",
        "Step away from the screen for 5 minutes 💖",
        "Eat something yummy today 🍓 you deserve it",
        "Stretch it out 🌷 your body works hard for you",
        "You are allowed to take up space 💅",
    ]
    await ctx.send(embed=doll_embed("🌸 Self Care Reminder", random.choice(tips)))


@bot.command()
async def vibe(ctx):
    vibes = [
        "Soft girl era 🎀",
        "Coquette energy activated 💖",
        "Main character moment ✨",
        "Ethereal doll vibes only 🌸",
        "Staying cozy and powerful 💅",
        "Romanticising life today 🌷",
        "Unbothered, moisturized, thriving 💎",
    ]
    await ctx.send(embed=doll_embed("✨ Current Vibe", random.choice(vibes)))


@bot.command()
async def menu(ctx):
    embed = doll_embed(
        "💖 Dollhouse Menu",
        "Your command guide ✨"
    )
    embed.add_field(
        name="💬 Community",
        value="!doll\n!selfcare\n!affirm\n!vibe",
        inline=False
    )
    embed.add_field(
        name="🔐 Access",
        value="!verify dollhouse\n!rules\n!roles",
        inline=False
    )
    embed.add_field(
        name="🎟️ Systems",
        value="!ticketpanel\n!order\n!level\n!leaderboard\n!rep",
        inline=False
    )
    embed.add_field(
        name="⚖️ Moderation",
        value="!warn\n!mute\n!ban\n!clear",
        inline=False
    )
    embed.set_footer(text="💅 Dollhouse • stay soft & powerful")
    await ctx.send(embed=embed)


@bot.command()
async def verify(ctx, *, answer=None):
    if answer != "dollhouse":
        return await ctx.send("❌ wrong")
    vr = discord.utils.get(ctx.guild.roles, name=VERIFY_ROLE)
    ur = discord.utils.get(ctx.guild.roles, name=UNVERIFIED_ROLE)
    if vr:
        await ctx.author.add_roles(vr)
    if ur:
        await ctx.author.remove_roles(ur)
    await ctx.message.delete()
    await ctx.send(embed=doll_embed("💖 Verified", "welcome 💋"), delete_after=5)


@bot.command()
async def sendverify(ctx):
    await ctx.send(embed=doll_embed("🔒 Verification Required", "Click the button below to enter 💖"), view=VerifyView())


@bot.command()
async def roles(ctx):
    embed = doll_embed(
        "🎀 Choose Your Roles",
        "React to get roles 💖\n\n🎮 = Gamer\n🎨 = Artist\n💬 = Chatty"
    )
    message = await ctx.send(embed=embed)
    for emoji in ["🎮", "🎨", "💬"]:
        await message.add_reaction(emoji)


@bot.command()
async def event(ctx):
    embed = doll_embed(
        "🎮 Game Night",
        "Vote for what we should play 💖\n\n🎮 Fortnite\n🧱 Minecraft\n🔫 COD\n👻 Phasmophobia\n\nClick below to join ✨"
    )
    message = await ctx.send(embed=embed, view=EventView("Game Night"))
    for emoji in ["🎮", "🧱", "🔫", "👻"]:
        await message.add_reaction(emoji)


@bot.command()
async def signups(ctx, *, event_name="Game Night"):
    total = get_event_signups(ctx.guild.id, event_name)
    await ctx.send(f"💖 **{event_name}** has **{total}** sign-up(s) so far!")


@bot.command()
async def xp(ctx, member: discord.Member = None):
    target = member or ctx.author
    points = get_xp_db(target.id)
    await ctx.send(f"✨ {target.mention} has **{points} XP** (Level {lvl(points)})")


@bot.command()
async def level(ctx, member: discord.Member = None):
    target = member or ctx.author
    points = get_xp_db(target.id)
    current_level = lvl(points)
    next_level_xp = (current_level + 1) * 50
    role_name = LEVEL_ROLES.get(current_level, "none yet")
    await ctx.send(embed=doll_embed(
        "💖 Level Check",
        f"{target.mention}\n**Level:** {current_level}\n**XP:** {points} / {next_level_xp}\n**Role:** {role_name}"
    ))


@bot.command()
async def rep(ctx, member: discord.Member = None):
    target = member or ctx.author
    mem = upsert_memory(target.id, ctx.guild.id, target.display_name)
    await ctx.send(embed=doll_embed(
        "💎 Rep",
        f"{target.mention} has **{mem['rep']} rep** 💖"
    ))


@bot.command()
async def leaderboard(ctx):
    rows = get_leaderboard(ctx.guild.id)
    text = ""
    for i, (user_id, xp_val) in enumerate(rows, 1):
        member = ctx.guild.get_member(user_id)
        if member:
            text += f"{i}. {member.display_name} — {xp_val} XP\n"
    await ctx.send(embed=doll_embed("💎 Top Dolls", text or "No data yet!"))


@bot.command()
async def ticketpanel(ctx):
    await ctx.send(embed=doll_embed("💌 Support", "open ticket ✨"), view=Ticket())


@bot.command()
async def close(ctx):
    settings = get_server_settings(ctx.guild.id)
    log_id   = settings.get("log_channel") or GIVEAWAY
    log      = ctx.guild.get_channel(log_id)
    msgs     = []
    async for m in ctx.channel.history(limit=100):
        msgs.append(f"{m.author}: {m.content}")
    file = discord.File(io.StringIO("\n".join(msgs)), filename="transcript.txt")
    if log:
        await log.send(
            embed=doll_embed("📋 Ticket Closed", f"Transcript for **{ctx.channel.name}**"),
            file=file
        )
    await ctx.channel.delete()


@bot.command()
async def lock(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send("🔒 Channel locked")


@bot.command()
async def unlock(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send("🔓 Channel unlocked")


@bot.command()
@commands.has_permissions(administrator=True)
async def addvip(ctx, user: discord.Member):
    premium.add(user.id)
    await ctx.send(f"{user.mention} VIP 💎")


@bot.command()
@commands.has_permissions(administrator=True)
async def addpremium(ctx, user: discord.Member):
    premium.add(user.id)
    await ctx.send(f"💎 {user.mention} is now premium!")


@bot.command()
async def embed(ctx, *, text):
    if ctx.author.id not in premium:
        await ctx.send("💎 Premium only feature")
        return
    await ctx.send(embed=discord.Embed(description=text, color=PINK))


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("💖 enter a valid number", delete_after=3)
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 cleaned {len(deleted)} messages 💅")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def dashboard(ctx):
    embed = doll_embed(
        "💖 Dollhouse Control Panel",
        "Manage your server setup ✨"
    )
    embed.add_field(
        name="🎀 Setup Commands",
        value=(
            "`!seteventchannel #channel`\n"
            "`!setwelcome #channel`\n"
            "`!setlogchannel #channel`\n"
            "`!setviprole @role`\n"
            "`!setverifyrole @role`"
        ),
        inline=False
    )

    settings = get_server_settings(ctx.guild.id)
    ev_ch  = f"<#{settings['event_channel']}>"   if settings["event_channel"]   else "not set"
    wl_ch  = f"<#{settings['welcome_channel']}>" if settings["welcome_channel"] else "not set"
    log_ch = f"<#{settings['log_channel']}>"     if settings["log_channel"]     else "not set"
    vip_r  = f"<@&{settings['vip_role']}>"       if settings["vip_role"]        else "not set"
    ver_r  = f"<@&{settings['verify_role']}>"    if settings["verify_role"]     else "not set"

    embed.add_field(
        name="⚙️ Current Settings",
        value=(
            f"📅 Event channel: {ev_ch}\n"
            f"👋 Welcome channel: {wl_ch}\n"
            f"📋 Log channel: {log_ch}\n"
            f"💎 VIP role: {vip_r}\n"
            f"🔒 Verify role: {ver_r}"
        ),
        inline=False
    )
    embed.add_field(
        name="💎 Systems",
        value="Verification • VIP • Levels • Tickets\nAll systems are active 💅",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def seteventchannel(ctx, channel: discord.TextChannel):
    update_server_setting(ctx.guild.id, "event_channel", channel.id)
    await ctx.send(f"💖 Event channel set to {channel.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    update_server_setting(ctx.guild.id, "welcome_channel", channel.id)
    await ctx.send(f"🎀 Welcome channel set to {channel.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setviprole(ctx, role: discord.Role):
    update_server_setting(ctx.guild.id, "vip_role", role.id)
    await ctx.send(f"💎 VIP role set to {role.name}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setverifyrole(ctx, role: discord.Role):
    update_server_setting(ctx.guild.id, "verify_role", role.id)
    await ctx.send(f"💖 Verify role set to {role.name}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setlogchannel(ctx, channel: discord.TextChannel):
    update_server_setting(ctx.guild.id, "log_channel", channel.id)
    await ctx.send(f"📋 Log channel set to {channel.mention}")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clearuser(ctx, member: discord.Member, amount: int):
    def check(m):
        return m.author == member

    deleted = await ctx.channel.purge(limit=amount, check=check)
    await ctx.send(
        f"💖 removed {len(deleted)} messages from {member.mention}",
        delete_after=3
    )


bot.run(os.environ["TOKEN"])
