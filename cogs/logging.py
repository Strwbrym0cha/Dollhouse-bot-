import discord
from discord.ext import commands

MOD_LOG_CHANNEL = 1487483760529244503
JOIN_LEAVE_LOG_CHANNEL = 1487483791818752200
MESSAGE_LOG_CHANNEL = 1487483832222486629
PUNISHMENT_LOG_CHANNEL = 1487483863360864347
BOT_LOG_CHANNEL = 1487483902477074532


def make_embed(title, description, color=discord.Color.from_rgb(255, 182, 193)):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="Dollhouse Logs")
    return embed


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, channel_id, embed):
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_log(
            BOT_LOG_CHANNEL,
            make_embed("🤖 Bot Online", f"Logged in as **{self.bot.user}**", discord.Color.green()),
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self.send_log(
            BOT_LOG_CHANNEL,
            make_embed(
                "✅ Command Used",
                f"Command: `!{ctx.command}`\nUser: {ctx.author.mention}\nChannel: {ctx.channel.mention}",
                discord.Color.green(),
            ),
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await self.send_log(
            BOT_LOG_CHANNEL,
            make_embed(
                "⚠️ Command Error",
                f"Command: `{ctx.message.content}`\nUser: {ctx.author.mention}\nError: `{error}`",
                discord.Color.orange(),
            ),
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(
            JOIN_LEAVE_LOG_CHANNEL,
            make_embed("📥 Member Joined", f"{member.mention}\nID: `{member.id}`", discord.Color.green()),
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            JOIN_LEAVE_LOG_CHANNEL,
            make_embed("📤 Member Left", f"{member}\nID: `{member.id}`", discord.Color.red()),
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        content = message.content or "No text content"
        if len(content) > 900:
            content = content[:900] + "..."

        await self.send_log(
            MESSAGE_LOG_CHANNEL,
            make_embed(
                "🗑️ Message Deleted",
                f"User: {message.author.mention}\nChannel: {message.channel.mention}\nMessage: {content}",
                discord.Color.red(),
            ),
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return

        old = before.content or "No text content"
        new = after.content or "No text content"
        if len(old) > 450:
            old = old[:450] + "..."
        if len(new) > 450:
            new = new[:450] + "..."

        await self.send_log(
            MESSAGE_LOG_CHANNEL,
            make_embed(
                "✏️ Message Edited",
                f"User: {before.author.mention}\nChannel: {before.channel.mention}\nBefore: {old}\nAfter: {new}",
                discord.Color.orange(),
            ),
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        added = [role.mention for role in after_roles - before_roles if role.name != "@everyone"]
        removed = [role.mention for role in before_roles - after_roles if role.name != "@everyone"]

        if not added and not removed:
            return

        parts = [f"Member: {after.mention}"]
        if added:
            parts.append(f"Added: {', '.join(added)}")
        if removed:
            parts.append(f"Removed: {', '.join(removed)}")

        await self.send_log(
            MOD_LOG_CHANNEL,
            make_embed("🎀 Roles Updated", "\n".join(parts), discord.Color.blurple()),
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(
            PUNISHMENT_LOG_CHANNEL,
            make_embed("🔨 Member Banned", f"User: {user}\nID: `{user.id}`", discord.Color.red()),
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log(
            PUNISHMENT_LOG_CHANNEL,
            make_embed("⚖️ Member Unbanned", f"User: {user}\nID: `{user.id}`", discord.Color.green()),
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log(
            MOD_LOG_CHANNEL,
            make_embed("➕ Channel Created", f"Channel: {channel.mention}\nID: `{channel.id}`", discord.Color.green()),
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log(
            MOD_LOG_CHANNEL,
            make_embed("➖ Channel Deleted", f"Channel: `{channel}`\nID: `{channel.id}`", discord.Color.red()),
        )


async def setup(bot):
    await bot.add_cog(Logging(bot))
