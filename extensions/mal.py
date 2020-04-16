from discord.ext import commands
from jikanpy import Jikan


jikan = Jikan()


@commands.command()
async def mal(ctx):
    ctx.send("wip")


def setup(bot):
    bot.add_command(mal)