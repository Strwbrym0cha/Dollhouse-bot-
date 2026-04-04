import discord
from discord.ext import commands
import os, asyncio
from cogs.general import EventView
from cogs.general import StaffView

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"💖 Logged in as {bot.user}")
    bot.add_view(EventView())
    bot.add_view(StaffView())
    
async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")
            except Exception as e:
                print(f"Failed {file}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

asyncio.run(main())
