import config # Config framework
from discord.ext import commands # Discord framework
import datetime # Used to determine weeknumber
import re # Regex library

class SotwNomination(object):

    # reusable regex definition to validate field input 
    def matchPattern(self, string, field):
        regex = rf"^{field}\:\s?(.*)"
        match = re.search(regex, string, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1), True
        else:
            return f"{field} is ongeldig", False

    async def validate(self, message):
        fields = ["artist", "title", "anime", "url"]
        errors = []
        for field in fields:
            result = self.matchPattern(message, field)
            if result[1] == False:
                errors.append(result[0])
        if len(errors) > 0: 
            return errors
        else:
            return message
        
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
    @commands.has_role(config.role['global_mod'])
    async def next(self, ctx, cmd):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['sotw'])
        role = next(r for r in user.guild.roles if r.id == config.role['user'])
        
        # Disable writes to the SOTW channel so we can declare a winner in a sane way
        await channel.set_permissions(role, send_messages=False, reason=f'Stopping sotw, triggered by {user.name}')
        
        
        # Get history of channel since last message from the bot
        messages = await channel.history().flatten()
        nominations = []
        for msg in reversed(messages):
            if msg.author == self.bot:
                break
            nominations.append(SotwNomination.validate(msg))
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
