import discord
from discord.ext import commands
import os, asyncio

# 💖 IMPORT ALL VIEWS
from cogs.general import (
    EventView,
    StaffView,
    AgeView,
    GenderView,
    LocationView,
    PronounView,
    SexualityView
)

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    # 💅 REGISTER PERSISTENT VIEWS
    bot.add_view(EventView())
    bot.add_view(StaffView())
    bot.add_view(AgeView())
    bot.add_view(GenderView())
    bot.add_view(LocationView())
    bot.add_view(PronounView())
    bot.add_view(SexualityView())


# 🔌 LOAD COGS
async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")
            except Exception as e:
                print(f"Failed {file}: {e}")


# 🚀 START BOT
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


asyncio.run(main())
