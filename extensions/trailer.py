from discord.ext import commands
from jikanpy import Jikan

jikan = Jikan()


@commands.command(help='Show anime trailer, wip')
async def trailer(ctx):
    await ctx.channel.send("soon (tm)")


def setup(bot):
    bot.add_command(trailer)
