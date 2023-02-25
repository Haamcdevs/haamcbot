import requests
from discord.ext import commands
from discord.ext.commands import Context
from jikanpy import Jikan
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache

import config
from anilist.anime import AnimeClient

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))
jikan = Jikan(session=session)


@commands.hybrid_command(help='Show anime trailer if available on MAL')
async def trailer(ctx: Context, search):
    anime = await AnimeClient().by_title(search)
    if anime is None:
        return await ctx.send(":x: Anime not found", ephemeral=True)
    if anime['trailer'] is not None:
        await ctx.channel.send(f":movie_camera: **{anime['name']}** trailer\n" + anime['trailer'])
        await ctx.send('loading', ephemeral=True)
        await ctx.interaction.delete_original_response()
        return
    await ctx.send(f":x: No trailer available for **{anime['title']}**",  ephemeral=True)


async def setup(bot):
    bot.add_command(trailer)
