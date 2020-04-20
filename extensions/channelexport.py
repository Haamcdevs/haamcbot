import sys
import io
import os
from discord import File
from discord.ext import commands
from discord.member import Member

@commands.command()
async def userexport(ctx, channelId: int): 
    channel = next(ch for ch in ctx.guild.channels if ch.id == channelId)  
    if channel is not None:
         await sendreadusersforchannel(ctx, channel)
    else:
        await ctx.send("Sorry, but that channel isn't real!")
 
async def sendreadusersforchannel(ctx, channel):
    output = io.StringIO()
    output.write(f"id,name{os.linesep}")
    hasFoundSomething = False
    for overwrite in channel.overwrites.items():       
        if type(overwrite[0]) is Member and not overwrite[0].bot and overwrite[1].read_messages:
            hasFoundSomething = True
            output.write(f'{overwrite[0].id},{overwrite[0].name}{os.linesep}')

    binary = io.BytesIO(output.getvalue().encode('utf-8'))  
    if hasFoundSomething:
        await ctx.send(f'Here is your export {ctx.author.mention}',file=File(binary,f"{channel.name}.csv"))
    else:
        await ctx.send(f'Could not find any users in that channel {ctx.author.mention}')

def setup(bot):
    bot.add_command(userexport)