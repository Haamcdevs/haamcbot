import io
import os

from discord import File
from discord.ext import commands

import config


@commands.command(help='Export a .csv of messages with their emoji count')
@commands.has_role(config.role['global_mod'])
async def export(ctx, channel_id: int = 0):
    try:
        channel = next(ch for ch in ctx.guild.channels if ch.id == channel_id)
    except StopIteration:
        channel = ctx.channel
        
    output = io.StringIO()
    output.write(f"emoji,count,message,author,createdat{os.linesep}")           

    messageswithReactions = list(filter(
        lambda o: len(o.reactions) > 0,
        [message async for message in channel.history(limit=100)]
    ))

    if not (messageswithReactions):
        await ctx.send(f'Could not find any messages with reactions in that channel {ctx.author.mention}')
        return   
    else:
       for message in messageswithReactions:
            reaction = max(message.reactions, key=lambda k: k.count)
            messageContent = message.content.replace(',','\,').replace('\n',' ')
            output.write(f"{reaction.emoji},{reaction.count},{messageContent},{message.author},{message.created_at}{os.linesep}")

    binary = io.BytesIO(output.getvalue().encode('utf-8'))
    await ctx.send(f'Here is your export {ctx.author.mention}', file=File(binary, f"{channel.name}.csv"))
    print(f'{ctx.author} exported {channel}')


def setup(bot):
    bot.add_command(export)
