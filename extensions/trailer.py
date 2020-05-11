import re

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


@commands.command(help='Show anime trailer if available on MAL')
async def trailer(ctx, *search):
    search = jikan.search('anime', ' '.join(search))
    if len(search['results']) == 0:
        return await ctx.channel.send(":x: Anime not found")
    anime_id = search['results'][0]['mal_id']
    anime = jikan.anime(anime_id)
    if trailer := anime['trailer_url']:
        if 'embed' in trailer:
            trailer = f"https://www.youtube.com/watch?v={re.search('/embed/([^?]+)', trailer)[1]}"
            return await ctx.channel.send(f":movie_camera: **{anime['title']}** trailer\n" + trailer)
    await ctx.channel.send(f":x: No trailer available for **{anime['title']}**")


def setup(bot):
    bot.add_command(trailer)
