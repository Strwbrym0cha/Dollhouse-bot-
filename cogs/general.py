from discord.ext import commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="💖 Dollhouse Commands",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🎮 General",
            value="!profile\n!leaderboard\n!daily",
            inline=False
        )

        embed.add_field(
            name="💰 Economy",
            value="!shop\n!buy",
            inline=False
        )

        embed.add_field(
            name="🎟️ Support",
            value="!ticketpanel",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
