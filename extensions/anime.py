import re
import textwrap

import discord
import requests
from discord.ext import commands
from AnilistPython import Anilist
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache

import config

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))

@commands.hybrid_command(help='Show anime information')
async def anime(ctx: discord.ext.commands.context.Context, search):
    anilist = Anilist()
    anime_id = anilist.get_anime_id(search)
    anime = anilist.get_anime(search)
    description_parts = textwrap.wrap(anime['desc'], 1000)
    embed = discord.Embed(type='rich', title=anime['name_romaji'])
    embed.set_thumbnail(url=anime['cover_image'])
    embed.set_author(icon_url='https://i.imgur.com/pcdrHvS.png', name="")
    for i, desc in enumerate(description_parts):
        embed.add_field(name=f'...', value=desc.replace('<br>','\n'), inline=False)
    embed.add_field(name=f'Episodes', value=anime['airing_episodes'])
    embed.add_field(name=f'Status', value=anime['airing_status'])
    embed.add_field(name=f'Score', value=anime['average_score'])
    if anime['next_airing_ep'] != None:
        airing_timestamp = anime['next_airing_ep']['airingAt']
        embed.add_field(name=f'Broadcast', value=f"<t:{airing_timestamp}>")
    embed.add_field(name=f'Premiered', value=anime['starting_time'])
    embed.add_field(name=f'Links', value=f"[AniList](https://anilist.co/anime/{anime_id})")
    await ctx.channel.send(embed=embed)
    print(ctx.interaction)
    #await ctx.message.delete()


async def setup(bot):
    bot.add_command(anime)
