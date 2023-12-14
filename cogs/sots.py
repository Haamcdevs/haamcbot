import re
import datetime
import operator
from typing import List

import discord
from discord import ui, Guild
from discord.app_commands import Choice
from discord.ext import commands
import mysql.connector
from discord.ext.commands import Context

import config

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)


class SotwNominationModal(ui.Modal, title='Song of the season'):
    nomination_artist = ui.TextInput(label='Artist', custom_id='artist')
    nomination_title = ui.TextInput(label='Title', custom_id='title')
    nomination_anime = ui.TextInput(label='Anime', custom_id='anime')
    nomination_youtube = ui.TextInput(label='Youtube link', custom_id='youtube')

    async def on_submit(self, interaction: discord.Interaction):
        if not re.match(r'.*youtu\.?be.*', self.nomination_youtube.value):
            await interaction.response.send_message(f':x: Invalid youtube link', ephemeral=True)
            return
        message = f'{self.nomination_youtube.value}\n' \
                  f'**Artist:** {self.nomination_artist.value}\n' \
                  f'**Title:** {self.nomination_title.value}\n' \
                  f'**Anime:** {self.nomination_anime.value}\n' \
                  f'**User:** {interaction.user.mention}\n'
        channel = interaction.guild.get_channel_or_thread(config.channel['sotw'])
        message = await channel.send(message)
        await message.add_reaction('🔼')
        await interaction.response.send_message(f'Nomination added to {channel.mention}', ephemeral=True)


class SotwNomination(object):
    def __init__(self, message: discord.message):
        self.message = message
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    def get_field_value(self, field):
        regex = rf"\*\*{field}\:\*\*([^\n]+)"
        content = self.message.content
        match = re.search(regex, content, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
        else:
            return None

    def get_username(self):
        guild: Guild = self.message.guild
        return guild.get_member(self.get_userid()).display_name

    def get_userid(self):
        matches = re.search('<@([0-9]+)+>', self.message.content)
        return int(matches.group(1)) or None

    def get_youtube_code(self):
        regex = rf"([\w-]*)$"
        match = re.search(regex, self.message.content, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1)
        else:
            return None

    def get_yt_url(self):
        code = self.get_youtube_code()
        return f'https://www.youtube.com/watch?v={code}'

    def get_winner_text(self, week):
        return f"\nWeek {week}: {self.get_field_value('Artist')} - " \
               f"{self.get_field_value('Title')} ({self.get_field_value('Anime')}) " \
               f"door {self.get_username()} - {self.get_yt_url()}\n"

    def get_bbcode(self):
        yt_code = self.get_youtube_code()
        return f"[spoiler=\"{self.votes} Votes ({self.get_username()}) :" \
               f" {self.get_field_value('Artist')}" \
               f" - {self.get_field_value('Title')} ({self.get_field_value('Anime')})\"]" \
               f"[yt]{yt_code}[/yt]" \
               f"[/spoiler]\n"

    def get_ranking_text(self, i: int):
        return f":radio: {i + 1}) **{self.get_field_value('Artist')}** - " \
               f"**{self.get_field_value('Title')}**\n" \
               f"votes: **{self.votes}** | " \
               f"anime: *{self.get_field_value('Anime')}* | " \
               f"door: {self.get_username()}\n"


class Sots(commands.Cog):
    # Init the command
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='sots', invoke_without_commands=True, help='Song of the season')
    async def sots(self, ctx):
        return

    async def get_ranked_nominations(self, ctx):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['sotw'])
        # Get history of channel since last message from the bot
        messages = [message async for message in channel.history(limit=100)]
        nominations = []
        for msg in messages:
            if msg.author.bot and re.match('.*De nominaties voor Song of the Season.*', msg.content):
                break
            nominations.append(SotwNomination(msg))
        nominations.sort(key=operator.attrgetter('votes'), reverse=True)
        return nominations

    async def forum(self, nominations: List[SotwNomination]):
        msg = '```'
        # msg += nominations[0].get_winner_text(self.get_previous_week_number())
        msg += '[spoiler]'
        for n in nominations:
            msg += n.get_bbcode()
        msg += f'[/spoiler]\n' \
               f'```\n' \
               f'<https://myanimelist.net/forum/?topicid=1680313>\n' \
               f'`t€scores add {nominations[0].get_userid()} 3000`\n' \
               f'`t€scores add {nominations[1].get_userid()} 2000`\n' \
               f'`t€scores add {nominations[2].get_userid()} 1000`\n' \
               f'<#{config.channel["sotw"]}>'
        return msg

    @sots.command(pass_context=True, help='Show the SOTS ranking')
    async def ranking(self, ctx):
        nominations = await self.get_ranked_nominations(ctx)
        msg = ''
        for i, nomination in enumerate(nominations):
            msg += nomination.get_ranking_text(i)
        if msg == '':
            await ctx.send(':x: No nominations', ephemeral=True)
            return
        # await ctx.channel.send(msg)
        await ctx.send(f'Here is the current song of the week ranking\n{msg}', ephemeral=True)

    @sots.command(pass_context=True, help='End a round of song of the season')
    @commands.has_role(config.role['global_mod'])
    async def finish(self, ctx: Context):
        print(f"user {ctx.author} ended song of the season")
        channel = ctx.guild.get_channel(config.channel['sotw'])
        nominations = await self.get_ranked_nominations(ctx)

        # TODO sort nominations by score AND date

        # Build a dict of the winner for the win message and database insertion
        winners = nominations[:3]
        await ctx.send(await self.forum(nominations))
        icons = {
            0: ':first_place:',
            1: ':second_place:',
            2: ':third_place:',

        }
        i = 0
        msg = ''
        for winner in winners:
            icon = icons[i]
            # Send the win message
            msg += f"{icon}  "\
                   f"{winner.get_field_value('Artist')} - "\
                   f"{winner.get_field_value('Title')} "\
                   f"({winner.get_field_value('Anime')}) "\
                   f"door <@{winner.get_userid()}> <{winner.get_yt_url()}>\n"
            await self.register_winner(
                winner.get_userid(),
                winner.get_field_value('Artist'),
                winner.get_field_value('Title'),
                winner.get_field_value('Anime'),
                winner.get_youtube_code(),
                winner.get_username(),
                winner.votes,
            )
            i = i+1
        await channel.send(msg)

    async def register_winner(
            self,
            userid: str,
            artist: str,
            title: str,
            anime: str,
            youtube_code: str,
            username: str,
            votes: int
    ):
        database.reconnect()
        # Open database before sending win message
        sotw_cursor = database.cursor()
        # Construct sql
        sql = "INSERT INTO sotw_winner (member_id, artist, title, anime, youtube, created, votes, display_name)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            userid,
            artist,
            title,
            anime,
            youtube_code,
            datetime.datetime.now(),
            votes,
            username
        )
        # Execute SQL
        sotw_cursor.execute(sql, val)
        # Commit change
        database.commit()

    @sots.command(pass_context=True, help='Make a nomination for song of the week')
    @commands.has_role(config.role['user'])
    async def nomination(self, ctx: Context):
        channel = ctx.guild.get_channel(config.channel['sotw'])
        messages = [message async for message in channel.history(limit=1)]
        for msg in messages:
            if msg.author.bot and re.match('.*:first_place:.*', msg.content):
                await ctx.reply(':x: Er is geen actieve ronde op dit moment!', ephemeral=True)
                return
        await ctx.interaction.response.send_modal(SotwNominationModal())

    @sots.command(pass_context=True, help='Start a new round of song of the season')
    @commands.has_role(config.role['global_mod'])
    async def start(self, ctx: Context, season: str, year: int):
        channel = ctx.guild.get_channel(config.channel['sotw'])
        await channel.send(
            f'De nominaties voor Song of the Season {season} {year} zijn geopend!'
            f'\nGebruik `/sots nomination` in een ander kanaal om te nomineren'
        )

    @start.autocomplete('season')
    async def category_autocomplete(self, ctx: Context, current: str) -> List[Choice[str]]:
        return [
            Choice(name='Winter', value='Winter'),
            Choice(name='Spring', value='Lente'),
            Choice(name='Summer', value='Zomer'),
            Choice(name='Fall', value='Herfst')
        ]


async def setup(bot):
    await bot.add_cog(Sots(bot))
