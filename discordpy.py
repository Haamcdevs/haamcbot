#!/usr/bin/env python3

import os
import time
import discord

from discord.ext import commands

import config

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=config.commandchar, description='Description', intents=intents.all())


@bot.event
async def on_ready():
    print(f'- Logging in: {bot.user.name} / {bot.user.id} -')

@bot.event
async def on_message(msg):
    # Writes logs away in folder logs/servername/channelname_date.log
    if config.logging_enabled:
        logfile = 'logs/{}/{}_{}.log'.format(msg.guild, msg.channel, time.strftime('%Y-%m-%d'))
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        with open(logfile, 'a') as log:
            log.write('{}  <{}> {}\n'.format(
                time.strftime('%Y-%m-%dT%H:%M:%S'),
                msg.author,
                msg.content.replace('\n', '\n    ')
            ))
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
