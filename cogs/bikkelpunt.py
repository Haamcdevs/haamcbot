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
        self.bikkelpunt_cursor = database.cursor()

    def is_time_correct(self):
        # If check time is not given, default to current UTC time
        check_time = datetime.utcnow().time()
        if check_time >= time(16, 00) and check_time <= time(20, 00):
            return True
        else:
            return False

    def has_cooldown(self, member_id):
        sql = f"SELECT last_update FROM bikkel where member_id = {member_id}"
        self.bikkelpunt_cursor.execute(sql)
        result = self.bikkelpunt_cursor.fetchall()
        for row in result:
            date = row
        today = datetime.today().date()
        print(date[0].date())
        print(today)
        if date[0].date() == today:
            return True
        return False

class Bikkelpunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name='bikkelpunt', invoke_without_commands=False)
    async def bikkelpunt(self, ctx):
        utils = Bikkelpunt_utils()
        check_time = utils.is_time_correct()
        has_cooldown = utils.has_cooldown(ctx.message.author.id)
        if check_time is False:
            await ctx.channel.send(
                f":last_quarter_moon_with_face: Echte bikkels leven tussen 03:00 en 05:00!"
                )
            return
        if has_cooldown is True:
            await ctx.channel.send(
                f":last_quarter_moon_with_face: Je hebt al gebikkelt vandaag, probeer het morgen nog eens"
            )
            return
        await ctx.channel.send(
            f":last_quarter_moon_with_face: Je bent een echte bikkel! **+1** (**%s** punten totaal)"
            )
def setup(bot):
    bot.add_cog(Bikkelpunt(bot))
