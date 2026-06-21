from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from utils import database

CENTRAL_TZ = ZoneInfo("America/Chicago")
DEFAULT_SCHEDULE_CHANNEL_ID = 1487481426705256661
SCHEDULE = {
    0: "Chill VC",
    2: "Game Night",
    4: "Community Event",
    6: "Movie Night",
}


def schedule_embed(event_name, details=None):
    description = f"**{event_name}** starts today. Come hang out with us!"
    if details:
        description = f"**{event_name}:** {details}\nCome hang out with us!"

    embed = discord.Embed(
        title="💖 Dollhouse Event Today",
        description=description,
        color=discord.Color.from_rgb(255, 182, 193),
    )
    embed.set_footer(text="Posted at 12 PM Central")
    return embed


class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.schedule_messages.start()

    def cog_unload(self):
        self.schedule_messages.cancel()

    def get_announcement_targets(self):
        targets = {
            guild_id: channel_id
            for guild_id, channel_id in database.get_schedule_channels()
        }

        default_channel = self.bot.get_channel(DEFAULT_SCHEDULE_CHANNEL_ID)
        if default_channel and default_channel.guild:
            targets.setdefault(default_channel.guild.id, DEFAULT_SCHEDULE_CHANNEL_ID)

        return targets.items()

    @tasks.loop(minutes=1)
    async def schedule_messages(self):
        now = datetime.now(CENTRAL_TZ)
        event_name = SCHEDULE.get(now.weekday())

        if not event_name or now.hour != 12 or now.minute > 4:
            return

        event_date = now.date().isoformat()

        for guild_id, channel_id in self.get_announcement_targets():
            event_details = None
            send_name = event_name
            if event_name == "Community Event":
                event_details = database.get_community_event(guild_id) or "Community Event"
                send_name = f"Community Event: {event_details}"

            if database.schedule_message_sent(guild_id, event_date, send_name):
                continue

            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            await channel.send(embed=schedule_embed(event_name, event_details))
            database.mark_schedule_message_sent(guild_id, event_date, send_name)

    @schedule_messages.before_loop
    async def before_schedule_messages(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setschedulechannel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        database.set_schedule_channel(ctx.guild.id, channel.id)
        await ctx.send(f"💖 schedule messages will post in {channel.mention} at 12 PM Central")

    @commands.command(aliases=["setevent", "setcommunity"])
    @commands.has_permissions(administrator=True)
    async def setcommunityevent(self, ctx, *, event_name: str):
        database.set_community_event(ctx.guild.id, event_name)
        await ctx.send(f"💖 Friday community event set to: **{event_name}**")

    @commands.command(aliases=["clearevent", "clearcommunity"])
    @commands.has_permissions(administrator=True)
    async def clearcommunityevent(self, ctx):
        database.clear_community_event(ctx.guild.id)
        await ctx.send("💖 Friday community event reset to the default Community Event")

    @commands.command()
    async def schedule(self, ctx):
        community_event = database.get_community_event(ctx.guild.id) or "Community Event"
        await ctx.send(
            embed=discord.Embed(
                title="🗓️ Dollhouse Schedule",
                description=(
                    "Monday: Chill VC\n"
                    "Wednesday: Game Night\n"
                    f"Friday: {community_event}\n"
                    "Sunday: Movie Night\n\n"
                    "Messages post at 12 PM Central."
                ),
                color=discord.Color.from_rgb(255, 182, 193),
            )
        )


async def setup(bot):
    await bot.add_cog(Schedule(bot))
