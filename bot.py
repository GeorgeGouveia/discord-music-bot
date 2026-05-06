import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from music import Music

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.add_cog(Music(bot))
    await bot.tree.sync()
    print(f"Bot online: {bot.user}")


bot.run(TOKEN)