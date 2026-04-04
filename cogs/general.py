from discord.ext import commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="💖 Dollhouse Commands",
            description="Everything you need ✨",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🎮 Fun",
            value="!leaderboard\n!rep @user",
            inline=False
        )

        embed.add_field(
            name="🎟️ Support",
            value="Use the ticket panel 💌",
            inline=False
        )

        embed.add_field(
            name="👑 Staff",
            value="!ticketpanel\n!clear\n!kick\n!ban",
            inline=False
        )

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(General(bot))
