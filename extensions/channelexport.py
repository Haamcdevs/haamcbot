import sys
import io
import os
from discord import File
from discord.ext import commands
from discord.member import Member

@commands.command()
async def userexport(ctx, channelId: int): 
    channel = getchannel(ctx, channelId)         
    if channel is not None:
         await sendreadusersforchannel(ctx, channel)
    else:
        await ctx.send("Sorry, but that channel isn't real!")

def getchannel(ctx, channelId: int):
    for channel in ctx.guild.channels:
        if channel.id == channelId:
           return channel
    return None

async def sendreadusersforchannel(ctx, channel):
    output = io.StringIO()
    output.write(f"id,name{os.linesep}")
    hasFoundSomething = False
    for overwrite in channel.overwrites.items():       
        if type(overwrite[0]) is Member and not overwrite[0].bot:
            if overwrite[1].read_messages:
                hasFoundSomething = True
                output.write(f'{overwrite[0].id},{overwrite[0].name}{os.linesep}')

    binary = io.BytesIO(output.getvalue().encode('utf-8'))  
    if hasFoundSomething:
        await ctx.send(f'Je hebt er jaren op moeten wachten, maar eindelijk heb ik een mooi lijste voor je xoxo {ctx.author.mention}',file=File(binary,f"{channel.name}.csv"))
    else:
        await ctx.send(f'Sorry schatje, maar ik heb niets kunnen vinden, kom je vanavond wel nog eten? {ctx.author.mention}')
def setup(bot):
    bot.add_command(channelexport)