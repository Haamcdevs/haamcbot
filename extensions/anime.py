import re
import textwrap

import discord
import requests
from discord.ext import commands
from jikanpy import Jikan, APIException
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache

import config

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))
jikan = Jikan(session=session)


@commands.command(help='Show anime information')
async def anime(ctx, *search):
    search = jikan.search('anime', ' '.join(search))
    if len(search['results']) == 0:
        return await ctx.channel.send(":x: Anime not found")
    anime_id = search['results'][0]['mal_id']
    anime = jikan.anime(anime_id)
    description_parts = textwrap.wrap(anime['synopsis'], 1000)
    genres = [g['name'] for g in anime['genres']]
    embed = discord.Embed(type='rich', title=anime['title'])
    embed.set_thumbnail(url=anime['image_url'])
    embed.set_author(icon_url='https://i.imgur.com/pcdrHvS.png', name="")
    for i, desc in enumerate(description_parts):
        embed.add_field(name=f'Description', value=desc, inline=False)
    embed.add_field(name=f'Episodes', value=anime['episodes'])
    embed.add_field(name=f'Status', value=anime['status'])
    embed.add_field(name=f'Score', value=anime['score'])
    embed.add_field(name=f'Popularity', value=anime['popularity'])
    embed.add_field(name=f'Broadcast', value=anime['broadcast'])
    embed.add_field(name=f'Premiered', value=anime['premiered'])
    embed.add_field(name=f'Source', value=anime['source'])
    embed.add_field(name=f'Genres', value=', '.join(genres))
    embed.add_field(name=f'Links', value=f"[MAL]({anime['url']})")
    await ctx.channel.send(embed=embed)


async def setup(bot):
    bot.add_command(anime)
