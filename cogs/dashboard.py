from discord.ext import commands
import discord

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dashboard(self, ctx):
        embed = discord.Embed(
            title="📊 Dollhouse Dashboard",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="💎 Systems",
            value="""
🎟️ Tickets: ✅  
💰 Economy: ✅  
💎 Leveling: ✅  
🛡️ Moderation: ✅  
""",
            inline=False
        )

        embed.add_field(
            name="📈 Server",
            value=f"Members: {ctx.guild.member_count}",
            inline=False
        )

        embed.set_footer(text="Dollhouse Co 💖")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
