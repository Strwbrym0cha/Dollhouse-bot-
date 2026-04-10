import datetime

import discord
from discord.ext import commands, tasks

from utils import database

WELCOME = 1487458364593017064
UNVERIFIED_ROLE = "Unverified Doll"
VERIFIED_ROLE = "Verified Doll"


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_unverified.start()

    def cog_unload(self):
        self.check_unverified.cancel()

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def personality(self, ctx, mode: str):
        mode = mode.lower()
        if mode not in {"soft", "sassy", "sweet", "strict"}:
            return await ctx.send("💖 modes: soft, sassy, sweet, strict")

        database.set_personality(ctx.guild.id, mode)
        await ctx.send(f"🎀 personality set to **{mode}** 💖")

    @commands.command()
    async def currentpersonality(self, ctx):
        mode = database.get_personality(ctx.guild.id)
        await ctx.send(f"💖 current personality: **{mode}**")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addvip(self, ctx, member: discord.Member):
        database.add_vip(member.id)
        await ctx.send(f"{member.mention} VIP 💎")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role = discord.utils.get(member.guild.roles, name=UNVERIFIED_ROLE)
        if role:
            await member.add_roles(role)

        channel = member.guild.get_channel(WELCOME)
        if channel:
            await channel.send(
                f"💖 {member.mention} welcome to the Dollhouse ✨\n🔐 Please verify to enter 💅"
            )

    @tasks.loop(minutes=5)
    async def check_unverified(self):
        for guild in self.bot.guilds:
            role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE)
            if not role:
                continue

            for member in guild.members:
                if role in member.roles and member.joined_at:
                    diff = (
                        datetime.datetime.utcnow() - member.joined_at.replace(tzinfo=None)
                    ).total_seconds()

                    if diff > 900:
                        try:
                            await member.kick(reason="Not verified in time")
                        except Exception:
                            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
