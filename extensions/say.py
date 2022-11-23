import config

from discord.ext import commands
from discord.ext.commands import Context


@commands.hybrid_command()
@commands.has_role(config.role['global_mod'])
async def say(ctx: Context, msg: str):
    await ctx.interaction.response.send_message('.', ephemeral=True)
    await ctx.interaction.delete_original_response()
    await ctx.channel.send(msg)


async def setup(bot):
    bot.add_command(say)
