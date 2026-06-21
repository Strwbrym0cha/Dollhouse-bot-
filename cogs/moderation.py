import datetime

import discord
from discord.ext import commands, tasks

from utils import database

WELCOME = 1487458364593017064
MOD_LOG_CHANNEL = 1487483760529244503
PUNISHMENT_LOG_CHANNEL = 1487483863360864347
UNVERIFIED_ROLE = "Unverified Doll"
VERIFIED_ROLE = "Verified Doll"


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_unverified.start()

    def cog_unload(self):
        self.check_unverified.cancel()

    async def send_log(self, channel_id, title, description, color=discord.Color.from_rgb(255, 182, 193)):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Dollhouse Logs")
        await channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await self.send_log(
            MOD_LOG_CHANNEL,
            "🧹 Messages Cleared",
            f"Moderator: {ctx.author.mention}\nChannel: {ctx.channel.mention}\nAmount: `{amount}`",
            discord.Color.orange(),
        )

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        reason = reason or "No reason provided"
        await member.kick(reason=reason)
        await self.send_log(
            PUNISHMENT_LOG_CHANNEL,
            "👢 Member Kicked",
            f"Moderator: {ctx.author.mention}\nMember: {member.mention}\nReason: {reason}",
            discord.Color.red(),
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        reason = reason or "No reason provided"
        await member.ban(reason=reason)
        await self.send_log(
            PUNISHMENT_LOG_CHANNEL,
            "🔨 Member Banned",
            f"Moderator: {ctx.author.mention}\nMember: {member.mention}\nReason: {reason}",
            discord.Color.red(),
        )

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
                            await self.send_log(
                                PUNISHMENT_LOG_CHANNEL,
                                "👢 Member Auto-Kicked",
                                f"Member: {member.mention}\nReason: Not verified in time",
                                discord.Color.red(),
                            )
                        except Exception:
                            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
