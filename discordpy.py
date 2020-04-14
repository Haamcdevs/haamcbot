#!/usr/bin/env python3
import config
from discord.ext import commands
import time


bot = commands.Bot(command_prefix='?', description='Description')


@bot.event
async def on_ready():
    print(f'- Logging in: {bot.user.name} / {bot.user.id} -')


# Extensions are python modulkes that contain various commands, cogs or listeners
@bot.command()
async def load(ctx, name: str):
    """Loads an extension from the extension folder"""
    try:
        if ctx.author in config.owners:
            bot.load_extension(f'extensions.{name}')
            await ctx.send(f'Loaded Extension {name}')
    except Exception as E:
        ctx.send(f'Extension {name} failed: {E}')



@bot.command()
async def loadcog(ctx, cog: str):
    """Loads a cog from the cogs folder"""
    pass


@bot.event
async def on_message(msg):
    # Writes logs away in folder logs/servername/channelname_date.log
    with open('logs/{}/{}_{}.log'.format(msg.guild, msg.channel, time.strftime('%Y-%m-%d')), 'a') as log:
        log.write('{}  <{}> {}\n'.format(time.strftime('%Y-%m-%dT%H:%M:%S'),
                                         msg.author, msg.content.replace('\n', '\n    ')))
    # Required to process commands
    await bot.process_commands(msg)


if __name__ == '__main__':
    for extension in config.extensions:
        bot.load_extension(f"extensions.{extension}")
    for cog in config.cogs:
        bot.load_extension(f"cogs.{cog}")
    bot.run(config.authkey)
