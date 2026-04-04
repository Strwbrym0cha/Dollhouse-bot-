from discord.ext import commands
import discord

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dashboard(self, ctx):
        embed = discord.Embed(
            title="📊 Dollhouse Dashboard",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="📈 Server Stats",
            value=f"Members: {ctx.guild.member_count}",
            inline=False
        )

        embed.add_field(
            name="⚙️ Systems",
            value="🎟️ Tickets ✅\n💎 Leveling ✅\n🛡️ Moderation ✅",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(YourCog(bot))
