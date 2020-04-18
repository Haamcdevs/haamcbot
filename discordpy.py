#!/usr/bin/env python3
import os
import config
from discord.ext import commands
import time


bot = commands.Bot(command_prefix=config.commandchar, description='Description')


@bot.event
async def on_ready():
    print(f'- Logging in: {bot.user.name} / {bot.user.id} -')


# Extensions are python modulkes that contain various commands, cogs or listeners
@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')


@bot.event
async def on_message(msg):
    # Writes logs away in folder logs/servername/channelname_date.log
    with open('logs/{}/{}_{}.log'.format(msg.guild, msg.channel, time.strftime('%Y-%m-%d')), 'a') as log:
        log.write('{}  <{}> {}\n'.format(time.strftime('%Y-%m-%dT%H:%M:%S'),
                                         msg.author, msg.content.replace('\n', '\n    ')))
    if msg.author.bot:
        return
    # Required to process commands
    await bot.process_commands(msg)


if __name__ == '__main__':
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded cogs.{filename[:-3]}')
    for filename in os.listdir('./extensions'):
        if filename.endswith('.py'):
            bot.load_extension(f'extensions.{filename[:-3]}')
            print(f'Loaded extensions.{filename[:-3]}')
    bot.run(config.authkey)
