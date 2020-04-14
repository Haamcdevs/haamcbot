import sys
import time
from discord.ext import commands

uptime = time.time()


@commands.command()
async def info(ctx):
    author = 'XSlicer#6364'
    lib = 'discord.py (0.16.5)'
    appsoft = sys.version.replace('\n','')
    runtime = time.time() - uptime
    days = int(runtime // 86400)
    hours = int(runtime // 3600 % 24)
    mins = int(runtime // 60 % 60)
    seconds = int(runtime % 60)
    runtime = "{} days, {} hours, {} mins, {} seconds".format(days, hours, mins, seconds)
    await ctx.send(f"**Info**\n- Author: {author}\n- Library: {lib}\n- Runtime: Python {appsoft}\n- Uptime: {runtime}")


def setup(bot):
    bot.add_command(info)
