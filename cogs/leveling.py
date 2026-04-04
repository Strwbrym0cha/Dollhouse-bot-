from discord.ext import commands
import random
from utils import database

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 👇 THIS IS on_message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        xp_gain = random.randint(5, 15)
        database.add_xp(message.author.id, xp_gain)

        level = database.check_level_up(message.author.id)

        if level:
            await message.channel.send(
                f"💖 {message.author.mention} leveled up to {level}!"
            )

        # 🚨 VERY IMPORTANT
        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
