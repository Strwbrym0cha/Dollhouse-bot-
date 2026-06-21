from datetime import datetime
import random
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from utils import database

CENTRAL_TZ = ZoneInfo("America/Chicago")
DEFAULT_QOTD_CHANNEL_ID = 1489465243913687160
QUESTIONS = [
    (1, "What's your comfort food?"),
    (2, "If you could visit any country tomorrow, where would you go?"),
    (3, "What's your favorite season and why?"),
    (4, "What's a hobby you'd love to learn?"),
    (5, "What's your favorite movie?"),
    (6, "What's your favorite anime?"),
    (7, "Cats, dogs, or another pet?"),
    (8, "What's your dream job?"),
    (9, "What song have you been listening to lately?"),
    (10, "What's your favorite color?"),
    (11, "What's your favorite holiday?"),
    (12, "Morning person or night owl?"),
    (13, "What's your favorite dessert?"),
    (14, "If money wasn't a concern, what would you buy first?"),
    (15, "What's your favorite game?"),
    (16, "What's your dream vacation?"),
    (17, "What's your favorite drink?"),
    (18, "What's your favorite fast food place?"),
    (19, "What fictional world would you live in?"),
    (20, "What's your favorite thing about yourself?"),
    (21, "What's a skill you're proud of?"),
    (22, "What was your first video game?"),
    (23, "What's your favorite animal?"),
    (24, "What's your favorite snack?"),
    (25, "What's your biggest pet peeve?"),
    (26, "If you had a superpower, what would it be?"),
    (27, "What's your favorite childhood memory?"),
    (28, "What makes you laugh every time?"),
    (29, "What's your favorite app?"),
    (30, "What language would you love to learn?"),
    (31, "What anime character are you most like?"),
    (32, "What's your favorite Disney movie?"),
    (33, "If you could instantly master one skill, what would it be?"),
    (34, "What's your favorite ice cream flavor?"),
    (35, "What would your dream house look like?"),
    (36, "What's your favorite holiday tradition?"),
    (37, "What's something on your bucket list?"),
    (38, "What's your favorite restaurant?"),
    (39, "What was your favorite subject in school?"),
    (40, "What's your favorite emoji?"),
    (41, "What's your favorite social media platform?"),
    (42, "What's a show you can watch over and over?"),
    (43, "If you won the lottery, what's the first thing you'd do?"),
    (44, "What's your favorite type of weather?"),
    (45, "What's a food you'll never eat again?"),
    (46, "What's your favorite mythical creature?"),
    (47, "What's your favorite board game?"),
    (48, "What was your first job?"),
    (49, "What's your favorite smell?"),
    (50, "What's your favorite thing to do on weekends?"),
    (51, "If you could have any pet, what would it be?"),
    (52, "What's your dream car?"),
    (53, "What's your favorite candy?"),
    (54, "What's a trend you actually like?"),
    (55, "What's your favorite flower?"),
    (56, "What's your favorite clothing style?"),
    (57, "What's a talent you'd love to have?"),
    (58, "What's your favorite holiday food?"),
    (59, "What's your favorite quote?"),
    (60, "What's one thing you're grateful for today?"),
    (61, "What's your dream cosplay?"),
    (62, "Which anime world would be the hardest to survive in?"),
    (63, "What's your favorite Pokemon?"),
    (64, "Which game have you spent the most hours in?"),
    (65, "What's your gaming comfort game?"),
    (66, "What's the best anime opening?"),
    (67, "Which fictional character would you be friends with?"),
    (68, "What's your favorite convention memory?"),
    (69, "What's your favorite cosplay you've done?"),
    (70, "What cosplay is next on your list?"),
    (71, "If you could live anywhere in the world, where would it be?"),
    (72, "What country do you most want to visit?"),
    (73, "What's your dream apartment aesthetic?"),
    (74, "Beach, mountains, city, or countryside?"),
    (75, "What's the most beautiful place you've seen?"),
    (76, "If you could teleport anywhere right now, where would you go?"),
    (77, "What culture would you love to learn more about?"),
    (78, "What's your dream travel destination?"),
    (79, "What's your favorite thing about traveling?"),
    (80, "What's one place everyone should visit?"),
    (81, "What's your ideal lazy day?"),
    (82, "If your life had a theme song, what would it be?"),
    (83, "What's your biggest goal this year?"),
    (84, "What's a small thing that makes you happy?"),
    (85, "What's your favorite memory from the last year?"),
    (86, "What's something you're looking forward to?"),
    (87, "What's your dream birthday celebration?"),
    (88, "What's your favorite way to relax?"),
    (89, "What's one thing you'd tell your younger self?"),
    (90, "What's something you've accomplished that you're proud of?"),
    (91, "If you owned a cafe, what would its theme be?"),
    (92, "If you had a magical companion, what would it be?"),
    (93, "What would your dream Discord server look like?"),
    (94, "If you could design your perfect day, what would happen?"),
    (95, "If you had a personal mascot, what would it be?"),
    (96, "What would you name your own kingdom?"),
    (97, "What would your dream bedroom look like?"),
    (98, "What's something you hope to experience one day?"),
    (99, "What's your favorite thing about being part of a community?"),
    (100, "What's one question you'd like to ask everyone here?"),
]


def qotd_message(number, question):
    return (
        f"🌸 Question of the Day #{number} 🌸\n\n"
        f"{question} 💖\n\n"
        "✨ Share your answer below, Pretty Dolls! ✨"
    )


class QuestionOfTheDay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_loop.start()

    def cog_unload(self):
        self.qotd_loop.cancel()

    def get_targets(self):
        targets = {
            guild_id: channel_id
            for guild_id, channel_id in database.get_qotd_channels()
        }

        default_channel = self.bot.get_channel(DEFAULT_QOTD_CHANNEL_ID)
        if default_channel and default_channel.guild:
            targets.setdefault(default_channel.guild.id, DEFAULT_QOTD_CHANNEL_ID)

        return targets.items()

    @tasks.loop(minutes=1)
    async def qotd_loop(self):
        now = datetime.now(CENTRAL_TZ)
        if now.hour != 10 or now.minute > 4:
            return

        post_date = now.date().isoformat()

        for guild_id, channel_id in self.get_targets():
            if database.qotd_sent(guild_id, post_date):
                continue

            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            number, question = random.choice(QUESTIONS)
            await channel.send(qotd_message(number, question))
            database.mark_qotd_sent(guild_id, post_date, number)

    @qotd_loop.before_loop
    async def before_qotd_loop(self):
        await self.bot.wait_until_ready()

    @commands.command()
    async def qotd(self, ctx):
        number, question = random.choice(QUESTIONS)
        await ctx.send(qotd_message(number, question))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setqotdchannel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        database.set_qotd_channel(ctx.guild.id, channel.id)
        await ctx.send(f"🌸 question of the day will post in {channel.mention} at 10 AM Central")


async def setup(bot):
    await bot.add_cog(QuestionOfTheDay(bot))
