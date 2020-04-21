import config # Config framework
from discord.ext import commands # Discord framework
import datetime # Used to determine weeknumber
import re # Regex library
import asyncio

class SotwNomination(object):
    def __init__(self, message):
        self.message = message
        try:
            self.votes = message.reactions[0].count - 1
        except IndexError:
            self.votes = 0

    # reusable regex definition to validate field input 
    def getFieldValue(self, string, field):
        regex = rf"^{field}\:\s?(.*)"
        match = re.search(regex, string, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1)
        else:
            return None

    async def validate(self, message):
        fields = ["artist", "title", "anime", "url"]
        errors = []
        for field in fields:
            result = self.getFieldValue(message.content, field)
            if result == None:
                errors.append(f"{field} is ongeldig")
        return errors

        
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

    @commands.group(name='sotw', invoke_without_commands=True)
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
        await channel.send(nominations)
        return nominations
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != config.channel['sotw']:
            return
        errors = []
        try:
            nomination = SotwNomination(message)
            errors = await nomination.validate(message)
        except Exception as e:
            print(e)
        if len(errors):
            error_message = await message.channel.send("\n:x: " + "\n:x: ".join(errors))
            await asyncio.sleep(5)
            await message.delete()
            await error_message.delete()
            return
        await message.add_reaction('🔼')

    @sotw.command(pass_context=True, help='find winner and start next round of SOTW')
    @commands.has_role(config.role['global_mod'])
    async def next(self, ctx):
        nominations = await self.get_ranked_nominations(ctx)
        if len(nominations) < 2:
            return await ctx.message.channel.send(':x: Niet genoeg nominations')
        if nominations[0].votes == nominations[1].votes:
            return await ctx.message.channel.send(':x: Het is een gelijke stand')
        winner = nominations[0]
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.channel['sotw'])
        role = next(r for r in user.guild.roles if r.id == config.role['user'])
        await ctx.message.channel.send(winner)
        # Disable writes to the SOTW channel so we can declare a winner in a sane way
        # this can be removed
        await channel.set_permissions(role, send_messages=False, reason=f'Stopping sotw, triggered by {user.name}')
        

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
        # this can be removed
        await channel.set_permissions(role, send_messages=True, reason=f'Starting sotw, triggered by {user.name}')

def setup(bot):
    bot.add_cog(Sotw(bot))
