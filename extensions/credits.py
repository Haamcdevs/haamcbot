import sys
import time

import discord
from discord.ext import commands

uptime = time.time()


@commands.hybrid_command(help='Shows bot credits')
async def credits(ctx):
    author = 'Haamc devs: https://github.com/Haamcdevs'
    v = discord.version_info
    lib = f'discord.py {v.major}.{v.minor}.{v.micro}-{v.releaselevel}'
    appsoft = sys.version.replace('\n', '')
    runtime = time.time() - uptime
    days = int(runtime // 86400)
    hours = int(runtime // 3600 % 24)
    mins = int(runtime // 60 % 60)
    seconds = int(runtime % 60)
    runtime = "{} days, {} hours, {} mins, {} seconds".format(days, hours, mins, seconds)
    await ctx.interaction.response.send_message(f"**Info**\n- Author: {author}\n- Library: {lib}\n- Runtime: Python {appsoft}\n- Uptime: {runtime}", ephemeral=True)
    print(f"{ctx.author} showed the bot credits <3")


async def setup(bot):
    bot.add_command(credits)
