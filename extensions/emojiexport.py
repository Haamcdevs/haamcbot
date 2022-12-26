import io
import os
from typing import List

import numpy as np
from discord import File, ChannelType
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import Context

import config


@commands.hybrid_command(help='Export a .csv of messages with their emoji count')
@commands.has_role(config.role['global_mod'])
async def export(ctx: Context, channel):
    channel = ctx.guild.get_channel_or_thread(int(channel))
    output = io.StringIO()
    output.write(f"emoji,count,message,author,createdat{os.linesep}")

    messages_with_reactions = list(filter(
        lambda o: len(o.reactions) > 0,
        [message async for message in channel.history(limit=100)]
    ))

    if not messages_with_reactions:
        await ctx.send(f'Could not find any messages with reactions in that channel {ctx.author.mention}', ephemeral=True)
        return
    else:
        for message in messages_with_reactions:
            reaction = max(message.reactions, key=lambda k: k.count)
            message_content = message.content.replace(',', ',').replace('\n', ' ')
            output.write(
                f"{reaction.emoji},{reaction.count},{message_content},{message.author},{message.created_at}{os.linesep}")

    binary = io.BytesIO(output.getvalue().encode('utf-8'))
    await ctx.send(f'Here is your export of <#{channel.id}>', file=File(binary, f"{channel.name}.csv"), ephemeral=True)
    print(f'{ctx.author} exported {channel}')


@export.autocomplete('channel')
async def channel_autocomplete(ctx: Context, current: str) -> List[Choice[str]]:

    channels = [
        Choice(name=channel.name, value=f'{channel.id}')
        for channel in ctx.guild.text_channels
        if channel.name.lower().__contains__(current.lower())
    ]
    threads = [
        Choice(name=thread.name, value=f'{thread.id}')
        for thread in ctx.guild.threads
        if thread.name.lower().__contains__(current.lower())
    ]

    return (channels + threads)[0:25]


async def setup(bot):
    bot.add_command(export)
