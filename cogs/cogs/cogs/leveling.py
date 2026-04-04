from discord.ext import commands
import random

xp = {}

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user = message.author.id
        xp[user] = xp.get(user, 0) + random.randint(5, 15)

def setup(bot):
    bot.add_cog(Leveling(bot))
