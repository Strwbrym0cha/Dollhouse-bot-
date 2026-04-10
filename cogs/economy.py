from discord.ext import commands
import discord
import random
from utils import database

PINK = discord.Color.from_rgb(255, 182, 193)


def embed(title, desc):
    e = discord.Embed(title=title, description=desc, color=PINK)
    e.set_footer(text="💖 Dollhouse")
    return e


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 💖 PROFILE
    @commands.command()
    async def profile(self, ctx):
        data = database.get_user(ctx.author.id)

        if not data:
            return await ctx.send("💔 no data found")

        xp, level, rep, coins = data[1], data[2], data[3], data[4]

        await ctx.send(embed=embed(
            "💖 Doll Profile",
            f"""
✨ Level: {level}
💎 XP: {xp}
💖 Rep: {rep}
💰 Coins: {coins}
"""
        ))

    # 🎁 DAILY REWARD
    @commands.command()
    async def daily(self, ctx):
        uid = str(ctx.author.id)

        if database.check_daily(uid):
            return await ctx.send("💖 come back later")

        xp = random.randint(50, 100)
        coins = random.randint(20, 50)

        database.give_daily(uid, xp, coins)

        await ctx.send(embed=embed(
            "🎁 Daily Reward",
            f"+{xp} XP\n+{coins} Coins 💰"
        ))

    # 🛍️ SHOP
    @commands.command()
    async def shop(self, ctx):
        await ctx.send(embed=embed(
            "🛍️ Dollhouse Shop",
            """
💎 100 coins — 🎀 Custom Role  
💎 200 coins — 👑 VIP (XP boost)  
💎 50 coins — 🌟 Featured Doll  
"""
        ))

    # 💰 BUY
    @commands.command()
    async def buy(self, ctx, item: str):
        uid = str(ctx.author.id)

        coins = database.get_coins(uid)

        if item.lower() == "vip":
            if coins < 200:
                return await ctx.send("💔 not enough coins")

            role = discord.utils.get(ctx.guild.roles, name="👑 VIP Doll")

            if role:
                await ctx.author.add_roles(role)

            database.remove_coins(uid, 200)

            await ctx.send("👑 VIP unlocked 💖")

        elif item.lower() == "featured":
            if coins < 50:
                return await ctx.send("💔 not enough coins")

            role = discord.utils.get(ctx.guild.roles, name="🌟 Featured Doll")

            if role:
                await ctx.author.add_roles(role)

            database.remove_coins(uid, 50)

            await ctx.send("🌟 you are now featured 💖")

        else:
            await ctx.send("💔 item not found")

    # 💸 BALANCE
    @commands.command()
    async def balance(self, ctx):
        coins = database.get_coins(str(ctx.author.id))

        await ctx.send(embed=embed(
            "💰 Your Balance",
            f"{coins} coins 💖"
        ))

    # 🎁 GIVE (ADMIN)
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def give(self, ctx, member: discord.Member, amount: int):
        database.add_coins(member.id, amount)

        await ctx.send(f"💖 gave {amount} coins to {member.mention}")

    # 🏆 LEADERBOARD (COINS)
    @commands.command()
    async def rich(self, ctx):
        top = database.get_top_coins()

        text = ""
        for i, (uid, coins) in enumerate(top, start=1):
            user = ctx.guild.get_member(int(uid))
            if user:
                text += f"{i}. {user.display_name} — {coins} 💰\n"

        await ctx.send(embed=embed("💰 Richest Dolls", text))

    # 💸 PAY
    @commands.command()
    async def pay(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("💔 amount must be positive")

        uid = str(ctx.author.id)
        target = str(member.id)

        if database.get_coins(uid) < amount:
            return await ctx.send("💔 not enough coins")

        database.remove_coins(uid, amount)
        database.add_coins(target, amount)
        await ctx.send(f"💖 paid {amount} coins to {member.mention}")

    # 🎲 GAMBLE
    @commands.command()
    async def gamble(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("💔 amount must be positive")

        uid = str(ctx.author.id)
        if database.get_coins(uid) < amount:
            return await ctx.send("💔 not enough coins")

        if random.random() < 0.5:
            database.remove_coins(uid, amount)
            await ctx.send(f"💔 you lost {amount} coins")
        else:
            database.add_coins(uid, amount)
            await ctx.send(f"🎉 you won {amount} coins")

    # 👑 ADMIN: SET COINS
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setcoins(self, ctx, member: discord.Member, amount: int):
        if amount < 0:
            return await ctx.send("💔 amount cannot be negative")

        database.set_coins(member.id, amount)
        await ctx.send(f"💖 set {member.mention} coins to {amount}")

    # 🧹 ADMIN: RESET USER
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetuser(self, ctx, member: discord.Member):
        database.reset_user(member.id)
        await ctx.send(f"💖 reset {member.mention}'s data")


async def setup(bot):
    await bot.add_cog(Economy(bot))
