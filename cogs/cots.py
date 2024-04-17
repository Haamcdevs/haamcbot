import re
import asyncio
import operator
from typing import List

import discord
import requests
from discord.app_commands import Choice
from discord.ext import commands
from discord.ext.commands import Context
from jikanpy import Jikan, APIException
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache

import config
from anilist.anime import AnimeClient

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))
jikan = Jikan(session=session)


class CotsNomination(object):
    def __init__(self, message, season):
        self.message = message
        self.season = season
        self.anime = None
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    def parse_id(self, match):
        try:
            return int(re.search(rf'anilist\.co/{match}/(\d+)', self.message.content)[1])
        except TypeError:
            return False

    async def get_anime(self):
        if self.anime is not None:
            return self.anime
        self.anime = await AnimeClient().by_id(self.parse_id('anime')) or False
        return self.anime

    async def get_character(self, anime):
        character = filter(lambda char: char['id'] == self.parse_id('character'), anime['characters'])
        for char in character:
            return char
        return None

    def is_character_in_anime(self, anime):
        character_id = self.parse_id('character')
        matches = filter(lambda char: char['id'] == character_id, anime['characters'])
        for match in matches:
            return True
        return False

    async def validate(self):
        errors = []
        if not self.parse_id('anime'):
            errors.append('Ongeldige anime link')
        if not self.parse_id('character'):
            errors.append('Ongeldige character link')
        if len(errors) > 0:
            return errors
        anime = await self.get_anime()
        if f"{anime['season']} {anime['season_year']}" != self.season:
            errors.append('Anime is niet in het correcte seizoen')
        if not self.is_character_in_anime(anime):
            errors.append(f'Character komt niet voor in de anime')
        return errors

    async def to_string(self):
        anime = await self.get_anime()
        character = await self.get_character(anime)
        #voice_actor = next(v for v in character['voice_actors'] if v['language'] == 'Japanese')
        return f":mens: **{character['name']}**, *{anime['name']}*" \
               f"\nvotes: **{self.votes}** | door: {self.message.author.display_name}"

    async def create_embed(self):
        anime = await self.get_anime()
        character = await self.get_character(anime)
        embed = discord.Embed(
            title=character['name'],
            url=f"https://anilist.co/character/{character['id']}"
        )
        anime_link = f"[{anime['name']}](https://anilist.co/anime/{anime['id']})"
        embed.add_field(name='Anime', value=anime_link, inline=False)
        embed.add_field(name='Description', value=character['description'], inline=False)
        embed.add_field(name='Nominated by', value=self.message.author.mention, inline=False)
        embed.set_image(url=character['image'])

        return embed

class RichCotsNomination(object):
    def __init__(self, message):
        self.message = message
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    def field(self, name):
        embed = self.message.embeds[0]
        for field in embed.fields:
            if field.name == name:
                return field.value
        return None

    def character(self):
        return self.message.embeds[0].title

    def anime(self):
        return self.unlink(self.field('Anime'))

    def author(self):
        return self.field('Nominated by')

    def character_link(self):
        return self.message.embeds[0].url

    def unlink(self, text):
        try:
            return re.search(r'\[(.*)]', text)[1]
        except TypeError:
            return False

    def to_string(self):
        anime = self.anime()
        character = self.character()
        author = self.author()

        return f":mens: **{character}**, *{anime}*" \
               f"\nvotes: **{self.votes}** | door: {author}"


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

    @commands.hybrid_group(name='cots', invoke_without_command=True, help='Character of the Season')
    async def cots(self, ctx):
        return

    async def get_ranked_nominations(self, ctx):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['cots'])
        messages = [message async for message in channel.history(limit=100)]
        nominations = []
        for msg in messages:
            if len(msg.reactions) == 0:
                break
            nominations.append(RichCotsNomination(msg))
        nominations.sort(key=operator.attrgetter('votes'), reverse=True)
        return nominations

    @cots.command(pass_context=True)
    @commands.has_role(config.role['global_mod'])
    async def start(self, ctx: Context, season: str, year: str):
        print(f'user {ctx.author} started character of the season {season} {year}')
        await ctx.send(f'Starting character of the season {season} {year}', ephemeral=True)
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['cots'])
        role = next(r for r in user.guild.roles if r.id == config.role['user'])
        season = f'{season} {year}'
        self.set_season(season)
        await channel.send(f"Bij deze zijn de nominaties voor season {season} geopend!")
        await channel.set_permissions(
            role,
            read_messages=True,
            send_messages=True,
            reason=f'Starting cots, triggered by {user.name}'
        )

    @start.autocomplete('season')
    async def category_autocomplete(self, ctx: Context, current: str) -> List[Choice[str]]:
        return [
            Choice(name='Winter', value='WINTER'),
            Choice(name='Spring', value='SPRING'),
            Choice(name='Summer', value='SUMMER'),
            Choice(name='Fall', value='FALL')
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != config.channel['cots']:
            return
        errors = []
        try:
            nomination = CotsNomination(message, self.get_season())
            errors = await nomination.validate()
        except APIException as e:
            print(e)
            errors.append('Er ging iets fout bij het ophalen van de anime of het character')
            return
        if len(errors):
            error_message = await message.channel.send("\n:x: " + "\n:x: ".join(errors))
            print(f"invalid cots nomination\n" + "\n".join(errors))
            await message.delete(delay=5)
            await error_message.delete(delay=5)
            return
        embed = await nomination.create_embed()
        embed_message = await message.channel.send(embed=embed)
        await embed_message.add_reaction('🔼')
        await message.delete()

    @cots.command()
    async def ranking(self, ctx, offset: int = 0):
        offset = offset * 10
        nominations = await self.get_ranked_nominations(ctx)
        nominations = nominations[offset:offset+10]
        nominations = enumerate(nominations)
        msg = []
        for i, n in nominations:
            ranking = i + offset + 1
            msg.append(f"{ranking}) " + n.to_string())
        if len(msg) == 0:
            await ctx.reply(':x: Geen nominaties met deze offset', ephemeral=True, delete_after=3)
            return
        await ctx.reply("\n".join(msg), ephemeral=True)

    @cots.command()
    @commands.has_role(config.role['global_mod'])
    async def finish(self, ctx: Context):
        print(f'user {ctx.author} finished character of the season')
        nominations = await self.get_ranked_nominations(ctx)
        if len(nominations) < 2:
            return await ctx.message.channel.send(':x: Niet genoeg nominations')
        if nominations[0].votes == nominations[1].votes:
            return await ctx.message.channel.send(':x: Het is een gelijke stand')
        winner = nominations[0]
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['cots'])
        role = next(r for r in user.guild.roles if r.id == config.role['user'])
        msg = []
        for i, n in enumerate(nominations):
            msg.append(f"{i + 1}) " + n.to_string())
            if len(msg) == 10:
                await channel.send("\n".join(msg))
                msg = []
        if len(msg) > 0:
            await channel.send("\n".join(msg))
        character = winner.character()
        character_link = winner.character_link()
        author = winner.author()
        anime = winner.anime()
        msg = f":trophy: Het character van {self.get_season()} is **{character}**! van {anime}\n" \
              f"Genomineerd door {author}\n" \
              f"{character_link}"
        await channel.send(msg)
        await channel.set_permissions(
            role,
            send_messages=False,
            read_messages=True,
            reason=f'Finishing cots, triggered by {user.name}'
        )
        await ctx.send('Character of the season finished', ephemeral=True)
        await ctx.interaction.delete_original_response()


async def setup(bot):
    await bot.add_cog(Cots(bot))
