import random

import discord
from discord.ext import commands

from utils import database

LEVEL_ROLES = {
    1: "porcelain doll",
    5: "ribbon doll",
    10: "velvet doll",
    15: "lace doll",
    20: "star doll",
    30: "royal doll",
    40: "diamond doll",
}

COUNT_CH = 1489330043510460547


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.count = 0
        self.last = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        uid = message.author.id
        database.ensure_user(uid, message.author.display_name)

        is_command = message.content.startswith("!")

        # Counting channel
        if not is_command and message.channel.id == COUNT_CH:
            if message.author == self.last:
                await message.delete()
                return

            try:
                n = int(message.content)
            except ValueError:
                await message.delete()
                return

            if n != self.count + 1:
                self.count = 0
                self.last = None
                await message.channel.send("💔 reset... start at 1 💖")
                return

            self.count = n
            self.last = message.author

            if self.count == 50:
                role = discord.utils.get(message.guild.roles, name="🌟 Featured Doll")
                if role and role not in message.author.roles:
                    await message.author.add_roles(role)

        # XP, rep, and personality responses only run on normal chat messages.
        if not is_command:
            gain = random.randint(2, 4)
            if database.is_vip(uid):
                gain += 2

            database.add_xp(uid, gain)
            database.add_rep(uid, 1)

            xp = database.get_xp(uid)
            level, current_level_xp, next_level_xp = database.get_level_info(xp)
            maybe_level = database.check_level_up(uid)

            if level in LEVEL_ROLES:
                role_name = LEVEL_ROLES[level]
                role = discord.utils.get(message.guild.roles, name=role_name)

                if role and role not in message.author.roles:
                    for old_name in LEVEL_ROLES.values():
                        old_role = discord.utils.get(message.guild.roles, name=old_name)
                        if old_role and old_role in message.author.roles:
                            await message.author.remove_roles(old_role)

                    await message.author.add_roles(role)

            if maybe_level:
                await message.channel.send(f"💖 {message.author.mention} leveled up to {maybe_level}!")

            mode = database.get_personality(message.guild.id)
            content = message.content.lower()

            if "sad" in content:
                if mode == "soft":
                    await message.channel.send(f"🧸 {message.author.display_name} I'm here for you 💖")
                elif mode == "sassy":
                    await message.channel.send("💅 stand up doll, you're too pretty to be sad")
                elif mode == "sweet":
                    await message.channel.send("💖 sending you hugs and love ✨")
                elif mode == "strict":
                    await message.channel.send("⚖️ focus. you got this.")

            if "lonely" in content:
                if mode == "soft":
                    await message.channel.send("💖 you're not alone here")
                elif mode == "sassy":
                    await message.channel.send("pls you have us, don't be dramatic 💅")

            # Soft mod for normal chat only.
            if message.content.isupper() and len(message.content) > 15:
                await message.delete()
                await message.channel.send("💖 keep it cute")

    @commands.command()
    async def level(self, ctx):
        xp = database.get_xp(ctx.author.id)
        level, current_level_xp, next_level_xp = database.get_level_info(xp)
        await ctx.send(f"💖 Level {level} | XP {xp - current_level_xp}/{next_level_xp - current_level_xp} ({xp} total)")

    @commands.command()
    async def rank(self, ctx):
        xp = database.get_xp(ctx.author.id)
        level, current_level_xp, next_level_xp = database.get_level_info(xp)
        await ctx.send(
            f"💖 Rank Card\n"
            f"Level: {level}\n"
            f"XP: {xp - current_level_xp}/{next_level_xp - current_level_xp}\n"
            f"Total XP: {xp}"
        )

    @commands.command()
    async def leaderboard(self, ctx):
        top = database.get_top_xp()

        text = ""
        for i, (uid, xp) in enumerate(top, start=1):
            member = ctx.guild.get_member(int(uid))
            if member:
                level, current_level_xp, next_level_xp = database.get_level_info(xp)
                text += f"{i}. {member.display_name} — Level {level} ({xp} XP)\n"

        await ctx.send(embed=discord.Embed(title="💎 Top Dolls", description=text or "No data yet 💖"))

    @commands.command()
    async def rep(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(f"💎 {member.display_name} rep: {database.get_rep(member.id)}")


async def setup(bot):
    await bot.add_cog(Leveling(bot))
