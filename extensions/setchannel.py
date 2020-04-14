from discord.ext import commands


@commands.command()
async def createchannel(ctx):
    await ctx.send(f'Hello {ctx.author.display_name}.')


def setup(bot):
    bot.add_command(createchannel)
