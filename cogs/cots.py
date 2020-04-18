import config
import re
import asyncio
from discord.ext import commands
from jikanpy import Jikan

jikan = Jikan()


class CotsNomination(object):
    def __init__(self, message, season):
        self.message = message
        self.season = season

    def get_anime_id(self):
        try:
            return int(re.search('anime/(\d+)' ,self.message)[1])
        except TypeError:
            return False

    def get_anime(self):
        return jikan.anime(self.get_anime_id())

    def get_character_id(self):
        try:
            return int(re.search('character/(\d+)' ,self.message)[1])
        except TypeError:
            return False

    def get_character(self):
        return jikan.character(self.get_character_id())

    @staticmethod
    def is_character_in_anime(character, anime):
        for a in character['animeography']:
            if anime['mal_id'] == a['mal_id']:
                return True
        return False

    def validate(self):
        errors = []
        if not self.get_anime_id():
            errors.append('Ongeldige anime link')
        if not self.get_character_id():
            errors.append('Ongeldige character link')
        if len(errors) > 0:
            return errors
        anime = self.get_anime()
        character = self.get_character()
        if anime['premiered'] != self.season:
            errors.append(f"Anime is niet premiered in {self.season} maar in {anime['premiered']}")
        if not self.is_character_in_anime(character, anime):
            errors.append(f'Character komt niet voor in de anime')
        return errors


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

    @commands.group(name='cots')
    @commands.has_role(config.role_global_mod)
    async def start(self, ctx, cmd, season: str, year: str):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.cots_channel)
        role = next(r for r in user.guild.roles if r.id == config.role_user)
        season = f'{season} {year}'
        self.set_season(season)
        await channel.send(f"Bij deze zijn de nominaties voor season {season} geopend!")
        await channel.set_permissions(role, send_messages=True, reason=f'Starting cots, triggered by {user.name}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != config.cots_channel:
            return
        nomination = CotsNomination(message.content, self.get_season())
        errors = nomination.validate()
        if len(errors):
            error_message = await message.channel.send("\n:x: " + "\n:x: ".join(errors))
            await asyncio.sleep(5)
            await message.delete()
            await error_message.delete()
            return
        await message.add_reaction('🔼')


def setup(bot):
    bot.add_cog(Cots(bot))
