import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and file != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")
            except Exception as e:
                print(f"Failed {file}: {e}")


async def main():
    if not TOKEN:
        raise RuntimeError("Missing TOKEN environment variable")

    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


asyncio.run(main())
