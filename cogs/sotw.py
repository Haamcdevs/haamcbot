from typing import List

import config
import discord
from discord.ext import commands
import datetime
import operator
import re
import mysql.connector

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)


class SotwNomination(object):
    def __init__(self, message: discord.message):
        self.message = message
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    def get_field_value(self, field):
        regex = rf"^{field}\:\s?(.*)"
        match = re.search(regex, self.message.content, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1)
        else:
            return None

    def get_username(self):
        return self.message.author.display_name

    def get_userid(self):
        return self.message.author.id

    def get_youtube_code(self):
        regex = rf"([\w]*)$"
        match = re.search(regex, self.get_field_value('url'), re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1)
        else:
            return None

    def get_yt_url(self):
        code = self.get_youtube_code()
        return f'https://www.youtube.com/watch?v={code}'

    async def validate(self):
        fields = ["artist", "title", "anime", "url"]
        errors = []
        for field in fields:
            result = self.get_field_value(field)
            if result is None:
                errors.append(f"{field} is ongeldig")
        return errors

    def get_winner_text(self, week):
        return f"\nWeek {week}: {self.get_field_value('artist')} - " \
               f"{self.get_field_value('title')} ({self.get_field_value('anime')}) " \
               f"door {self.message.author.display_name} - {self.get_yt_url()}\n"

    def get_bbcode(self):
        yt_code = self.get_youtube_code()
        return f"[spoiler=\"{self.votes} Votes ({self.message.author.display_name}) :" \
               f" {self.get_field_value('artist')}" \
               f" - {self.get_field_value('title')} ({self.get_field_value('anime')})\"]" \
               f"[yt]{yt_code}[/yt]" \
               f"[/spoiler]\n"


class Sotw(commands.Cog):
    # Init the command
    def __init__(self, bot):
        self.bot = bot

    # Get week number
    @staticmethod
    def get_week_number():
        d = datetime.datetime.today()
        number = datetime.date(d.year, d.month, d.day).isocalendar()[1]
        return number

    @commands.group(name='sotw', invoke_without_commands=True, help='Song of the week')
    @commands.has_role(config.role['global_mod'])
    async def sotw(self, ctx):
        return

    async def get_ranked_nominations(self, ctx):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['sotw'])
        # Get history of channel since last message from the bot
        messages = await channel.history(limit=100).flatten()
        nominations = []
        for msg in messages:
            if msg.author.bot:
                break
            nominations.append(SotwNomination(msg))
        nominations.sort(key=operator.attrgetter('votes'), reverse=True)
        return nominations

    async def forum(self, nominations: List[SotwNomination]):
        msg = '```'
        msg += nominations[0].get_winner_text(self.get_week_number())
        msg += '[spoiler]'
        for n in nominations:
            msg += n.get_bbcode()
        msg += f'[/spoiler]\n' \
               f'```\n' \
               f'<https://myanimelist.net/forum/?topicid=1680313>\n' \
               f'`t€scores add {nominations[0].message.author.id} 1500`'
        return msg

    # Listen for nominations in the SOTW channel
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != config.channel['sotw']:
            return
        print(f"user {message.author} submitted sotw nomination\n\n{message.content}\n")
        errors = []
        try:
            nomination = SotwNomination(message)
            errors = await nomination.validate()
        except Exception as e:
            print(e)
        if len(errors):
            error_message = await message.channel.send("\n:x: " + "\n:x: ".join(errors))
            await message.delete(delay=5)
            await error_message.delete(delay=5)
            print(f"user {message.author}'s sotw nomination was invalid: " + "\n".join(errors))
            return
        print(f"user {message.author}'s sotw nomination is valid")
        await message.add_reaction('🔼')

    @sotw.command(pass_context=True, help='Announce the winner and start next round of SOTW')
    @commands.has_role(config.role['global_mod'])
    async def next(self, ctx):
        print(f"user {ctx.author} started next song of the week round")
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['sotw'])
        nominations = await self.get_ranked_nominations(ctx)

        # Check if we have enough nominations and if we have a solid win 
        if len(nominations) < 2:
            return await ctx.channel.send(':x: Niet genoeg nominations')
        if nominations[0].votes == nominations[1].votes:
            return await ctx.channel.send(':x: Het is een gelijke stand')

        # Build a dict of the winner for the win message and database insertion
        winner = nominations[0]
        await ctx.channel.send(await self.forum(nominations))

        # Send the win message
        await channel.send(
            f":trophy: De winnaar van week {self.get_week_number() - 1} is: "
            f"{winner.get_field_value('artist')} - "
            f"{winner.get_field_value('title')} "
            f"({winner.get_field_value('anime')}) "
            f"door {winner.message.author.mention} <{winner.get_yt_url()}>")

        # Send the start of the new nomination week
        await channel.send(
            f":musical_note: :musical_note: Bij deze zijn de nominaties voor week"
            f" {self.get_week_number()} geopend! :musical_note: :musical_note:\n"
            f"Nomineer volgens onderstaande template (kopieer en plak deze, en zet er dan de gegevens in):\n"
            f"```\n"
            f"artist: \n"
            f"title: \n"
            f"anime:  \n"
            f"url: \n"
            f"```\n"
        )

        # Open database before sending win message
        sotw_cursor = database.cursor()

        # Construct sql
        sql = "INSERT INTO sotw_winner (member_id, artist, title, anime, youtube, created, votes, display_name)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            winner.get_userid(),
            winner.get_field_value('artist'),
            winner.get_field_value('title'),
            winner.get_field_value('anime'),
            winner.get_youtube_code(),
            datetime.datetime.now(),
            winner.votes,
            winner.get_username()
        )

        # Execute SQL
        sotw_cursor.execute(sql, val)

        # Commit change
        database.commit()


def setup(bot):
    bot.add_cog(Sotw(bot))
