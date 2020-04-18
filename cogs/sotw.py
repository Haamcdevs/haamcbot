import config
from discord.ext import commands
import datetime


class SotwNomination(object):

    def matchPattern(string)
        # regex: /^%s\:\s?(.*)/im
        # %s is name of the field, e.g.: artists or title


    def validate(self):
        errors = []
        # split message in fields
        # pass fields through validator
        # if fail, add to errors list
        # return list


class Sotw(commands.Cog):
    # Init the command
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def getWeeknumber():
        d = datetime.datetime.today()
        number = datetime.date(d.year, d.month, d.day).isocalendar()[1]
        return number

    # @commands.group(name='sotw')
    # @commands.Cog.listener()
    # async def fromMessage()

    @commands.group(name='sotw')
    @commands.has_role(config.role_global_mod)
    async def next(self, ctx, cmd):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.sotw_channel)
        role = next(r for r in user.guild.roles if r.id == config.role_user)
        
        # Disable writes to the SOTW channel so we can declare a winner in a sane way
        await channel.set_permissions(role, send_messages=False, reason=f'Stopping sotw, triggered by {user.name}')
        
        
        # Get history of channel since last message from the bot
        messages = await channel.history().flatten()
        nominations = []
        for msg in reversed(messages):
            if msg.author == self.bot:
                break
            nominations.append(SotwNomination(msg))
        await channel.send(nominations)

        # Send the start of the new nomination week
        await channel.send(f"""
:musical_note: :musical_note: Bij deze zijn de nominaties voor week {self.getWeeknumber()} geopend! :musical_note: :musical_note:
Nomineer volgens onderstaande template (kopieer en plak deze, en zet er dan de gegevens in):
```
artist: 
title: 
anime:  
url: 
```
""")
        # Re-enable writes to the channel to allow new nominations from users
        await channel.set_permissions(role, send_messages=True, reason=f'Starting sotw, triggered by {user.name}')

def setup(bot):
    bot.add_cog(Sotw(bot))
