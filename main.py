# 💖 IMPORTS
import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"💖 Logged in as {bot.user}")

# Load cogs
for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        try:
            bot.load_extension(f"cogs.{file[:-3]}")
            print(f"Loaded {file}")
        except Exception as e:
            print(f"Failed to load {file}: {e}")
bot.run(os.getenv("TOKEN"))
