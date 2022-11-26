import io
import os
from typing import List

from discord import File, ChannelType
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import Context
from discord.member import Member

import config


@commands.hybrid_command(help='Export a .csv of users who joined a joinable channel')
@commands.has_role(config.role['global_mod'])
async def userexport(ctx: Context, channel):
    channel = ctx.guild.get_channel(int(channel))
    output = io.StringIO()
    output.write(f"id,name{os.linesep}")
    joined_members = list(filter(
        lambda o: type(o[0]) is Member and not o[0].bot and o[1].read_messages,
        channel.overwrites.items()
    ))
    if not bool(joined_members):
        await ctx.send(f'Could not find any users in that channel {ctx.author.mention}')
        return
    for overwrite in joined_members:
        output.write(f'{overwrite[0].id},{overwrite[0].name}{os.linesep}')
    binary = io.BytesIO(output.getvalue().encode('utf-8'))
    await ctx.send(f'Here is your export for <#{channel.id}>', file=File(binary, f"{channel.name}.csv"), ephemeral=True)
    print(f"{ctx.author} exported users for channel {channel}")


@userexport.autocomplete('channel')
async def channel_autocomplete(ctx: Context, current: str) -> List[Choice[str]]:
    return [
        Choice(name=category.name, value=f'{category.id}')
        for category in ctx.guild.channels
        if category.type == ChannelType.text and category.name.lower().__contains__(current.lower())
    ][0:25]


async def setup(bot):
    bot.add_command(userexport)
