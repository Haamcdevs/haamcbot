from datetime import datetime, time

import mysql.connector
import pytz
import discord
from discord.ext import commands

import config

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)


class BikkelpuntUtils(object):
    def __init__(self):
        self.bikkelpunt_cursor = database.cursor(dictionary=True)

    def is_time_correct(self):
        date = datetime.now(pytz.timezone('Europe/Amsterdam'))
        check_time = date.time()
        return time(3, 00) <= check_time <= time(5, 00)

    def get_existing_record(self, member_id):
        sql = f"SELECT * FROM bikkel where member_id = {member_id}"
        self.bikkelpunt_cursor.execute(sql)
        return self.bikkelpunt_cursor.fetchone()

    def has_cooldown(self, record):
        today = datetime.today().date()
        if record.get('last_update').date() == today:
            return True
        return False

    def create_bikkelpunt_record(self, message):
        sql = "INSERT INTO bikkel (member_id, points, last_update, display_name)" \
              " VALUES (%s, %s, %s, %s)"
        val = (
            message.author.id,
            0,
            datetime.utcnow(),
            message.author.display_name
        )
        # Execute SQL
        self.bikkelpunt_cursor.execute(sql, val)

        # Commit change
        database.commit()

    def update_bikkelpunt_record(self, message, current_points):
        sql = "UPDATE bikkel SET points = %s, last_update = %s, display_name = %s WHERE member_id = %s"
        val = (
            current_points + 1,
            datetime.utcnow(),
            message.author.display_name,
            message.author.id
        )
        # Execute SQL
        self.bikkelpunt_cursor.execute(sql, val)

        # Commit change
        database.commit()

    def load_top_10(self):
        sql = 'SELECT * FROM bikkel ORDER BY points DESC LIMIT 0,10'
        self.bikkelpunt_cursor.execute(sql)
        return self.bikkelpunt_cursor.fetchall()

    def get_top_10_message(self):
        msg = ":last_quarter_moon_with_face: **HAAMC Discord bikkel ranking** *top 10*\n"
        for i, bikkel in enumerate(self.load_top_10()):
            msg += f"#{i + 1} **{bikkel['display_name']}** met **{bikkel['points']}** punten\n"
        return msg


class Bikkelpunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = BikkelpuntUtils()

    @commands.group(name='bikkel', invoke_without_commands=False, help='Bikkel punten')
    async def bikkel(self, ctx):
        return

    @bikkel.command(pass_context=True, help='Verdien een bikkelpunt')
    async def get(self, ctx):
        database.reconnect()
        # first check if the time is right before doing anything else
        check_time = self.utils.is_time_correct()
        if check_time is False:
            return await ctx.channel.send(
                f":last_quarter_moon_with_face: Echte bikkels leven tussen 03:00 en 05:00!"
            )
        record = self.utils.get_existing_record(ctx.message.author.id)
        if record is None:
            self.utils.create_bikkelpunt_record(ctx.message)
            record = self.utils.get_existing_record(ctx.message.author.id)
        else:
            if self.utils.has_cooldown(record):
                return await ctx.channel.send(
                    f":last_quarter_moon_with_face: Je hebt al gebikkelt vandaag, probeer het morgen nog eens"
                )
        self.utils.update_bikkelpunt_record(ctx.message, record.get('points'))
        await ctx.channel.send(
            f":last_quarter_moon_with_face: Je bent een echte bikkel! "
            f"**+1** (**{record.get('points') + 1}** punten totaal)"
        )

    @bikkel.command(help='Toon de top 10 bikkelpunten')
    async def ranking(self, ctx):
        database.reconnect()
        await ctx.channel.send(self.utils.get_top_10_message())


async def setup(bot):
    await bot.add_cog(Bikkelpunt(bot))
