from discord.ext import commands
import random
from utils import database

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        xp_gain = random.randint(5, 15)
        database.add_xp(message.author.id, xp_gain)

def setup(bot):
    bot.add_cog(Leveling(bot))
@commands.command()
async def leaderboard(self, ctx):
    database.cur.execute(
        "SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 10"
    )
    results = database.cur.fetchall()

    text = ""
    for i, (user_id, xp) in enumerate(results, start=1):
        user = ctx.guild.get_member(int(user_id))
        name = user.name if user else "Unknown"
        text += f"{i}. {name} — {xp} XP\n"

    await ctx.send(f"🏆 Leaderboard:\n{text}")
