import config
import re
import asyncio
import operator
from discord.ext import commands
import requests
from jikanpy import Jikan
from jikanpy import APIException
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))
jikan = Jikan(session=session)


class CotsNomination(object):
    def __init__(self, message, season):
        self.message = message
        self.season = season
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    def get_anime_id(self):
        try:
            return int(re.search('anime/(\d+)', self.message.content)[1])
        except TypeError:
            return False

    async def get_anime(self):
        try:
            return jikan.anime(self.get_anime_id())
        except APIException:
            await asyncio.sleep(0.5)
            return self.get_anime()

    def get_character_id(self):
        try:
            return int(re.search('character/(\d+)', self.message.content)[1])
        except TypeError:
            return False

    async def get_character(self):
        try:
            return jikan.character(self.get_character_id())
        except APIException:
            await asyncio.sleep(0.5)
            return self.get_character()

    @staticmethod
    def is_character_in_anime(character, anime):
        for a in character['animeography']:
            if anime['mal_id'] == a['mal_id']:
                return True
        return False

    async def validate(self):
        errors = []
        if not self.get_anime_id():
            errors.append('Ongeldige anime link')
        if not self.get_character_id():
            errors.append('Ongeldige character link')
        if len(errors) > 0:
            return errors
        anime = await self.get_anime()
        character = await self.get_character()
        if anime['premiered'] != self.season:
            errors.append(f"Anime is niet premiered in {self.season} maar in {anime['premiered']}")
        if not self.is_character_in_anime(character, anime):
            errors.append(f'Character komt niet voor in de anime')
        return errors

    async def to_string(self):
        character = await self.get_character()
        anime = await self.get_anime()
        voice_actor = next(v for v in character['voice_actors'] if v['language'] == 'Japanese')
        return f":mens: **{character['name']}**, *{anime['title']}*" \
               f"\nvotes: **{self.votes}** | door: {self.message.author.name} | " \
               f"voice actor: {voice_actor['name']} | score {anime['score']}"


class Cots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def set_season(season: str):
        with open('./var/cots_season', 'w+') as fd:
            fd.write(season)

    @staticmethod
    def get_season():
        with open('./var/cots_season', 'r') as fd:
            return fd.read()

    @commands.group(name='cots', invoke_without_command=True)
    async def cots(self):
        return

    async def get_ranked_nominations(self, ctx):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['cots'])
        messages = await channel.history(limit=100).flatten()
        nominations = []
        for msg in messages:
            if msg.author.bot:
                break
            nominations.append(CotsNomination(msg, self.get_season()))
        nominations.sort(key=operator.attrgetter('votes'), reverse=True)
        return nominations

    @cots.command()
    @commands.has_role(config.role['global_mod'])
    async def start(self, ctx, season: str, year: str):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['cots'])
        role = next(r for r in user.guild.roles if r.id == config.role['user'])
        season = f'{season} {year}'
        self.set_season(season)
        await channel.send(f"Bij deze zijn de nominaties voor season {season} geopend!")
        await channel.set_permissions(role, send_messages=True, reason=f'Starting cots, triggered by {user.name}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != config.channel['cots']:
            return
        nomination = CotsNomination(message, self.get_season())
        errors = await nomination.validate()
        if len(errors):
            error_message = await message.channel.send("\n:x: " + "\n:x: ".join(errors))
            await asyncio.sleep(5)
            await message.delete()
            await error_message.delete()
            return
        await message.add_reaction('🔼')

    @cots.command()
    async def ranking(self, ctx):
        nominations = await self.get_ranked_nominations(ctx)
        msg = []
        for i, n in enumerate(nominations):
            msg.append(f"{i + 1}) " + await n.to_string())
        await ctx.message.channel.send("\n".join(msg))


def setup(bot):
    bot.add_cog(Cots(bot))
