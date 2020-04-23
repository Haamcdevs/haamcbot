import config
import discord
from discord.ext import commands
from datetime import datetime, time
import mysql.connector

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)

class Bikkelpunt_utils(object):
    def __init__(self):
        self.bikkelpunt_cursor = database.cursor(dictionary=True)

    def is_time_correct(self):
        # If check time is not given, default to current UTC time
        # check_time = datetime.astimezone('Europe/Amsterdam')
        check_time = datetime.utcnow().time()
        if check_time >= time(16, 00) and check_time <= time(20, 00):
            return True
        else:
            return False

    def get_existing_record(self, member_id):
        sql = f"SELECT * FROM bikkel where member_id = {member_id}"
        self.bikkelpunt_cursor.execute(sql)
        return self.bikkelpunt_cursor.fetchone()

    def has_cooldown(self, result):
        today = datetime.today().date()
        print(result)
        if result[3].date() == today:
            return True
        return False
    
    def create_bikkelpunt_record(self, message):
        sql = "INSERT INTO bikkel (member_id, points, last_update, display_name)" \
              " VALUES (%s, %s, %s, %s)"
        val = (
            message.author.id,
            1,
            datetime.utcnow(),
            message.author.display_name
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
        for bikkel in self.load_top_10():
            print(bikkel)
            msg += f"{bikkel['display_name']}\n"
        return msg


class Bikkelpunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.utils = Bikkelpunt_utils()
    
    @commands.group(name='bikkel', invoke_without_commands=False, help='Bikkel punten')
    async def bikkel(self, ctx):
        return

    @bikkel.command(pass_context=True, help='Verdien een bikkelpunt')
    async def get(self, ctx):
        # first check if the time is right before doing anything else
        check_time = self.utils.is_time_correct()
        if check_time is False:
            await ctx.channel.send(
                f":last_quarter_moon_with_face: Echte bikkels leven tussen 03:00 en 05:00!"
                )
            return
        record = self.utils.get_existing_record(ctx.message.author.id)
        if record is None:
            self.utils.create_bikkelpunt_record(ctx.message)
        else:
            has_cooldown = self.utils.has_cooldown(record)
            if has_cooldown:
                await ctx.channel.send(
                    f":last_quarter_moon_with_face: Je hebt al gebikkelt vandaag, probeer het morgen nog eens"
                )
                return
        await ctx.channel.send(
            f":last_quarter_moon_with_face: Je bent een echte bikkel! **+1** (**{record.get[2]+1}** punten totaal)"
            )

    @bikkel.command()
    async def ranking(self, ctx):
        await ctx.channel.send(self.utils.get_top_10_message())


def setup(bot):
    bot.add_cog(Bikkelpunt(bot))
