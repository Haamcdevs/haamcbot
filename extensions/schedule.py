import time
from discord import NotFound
from discord.ext import commands
from discord.ext.commands import Context
from util.airing import Airing


@commands.hybrid_command(help='Show anime schedule', category='Anime')
async def schedule(ctx: Context, day_offset: int = None):
    airing = Airing()
    time_str = 'voor deze week'
    if day_offset is not None:
        day_in_seconds = 60 * 60 * 24
        start = int(time.time()) + day_offset * day_in_seconds
        end = start + day_in_seconds
        time_str = f'van <t:{start}:R> tot <t:{end}:R>'
    messages = [f'Animerooster {time_str}']
    upcoming_episodes = airing.load_upcoming(24 * 7, day_offset)
    if len(upcoming_episodes) == 0:
        await ctx.send(f'Geen airing data gevonden voor {time_str}', ephemeral=True)
        return
    for episode in upcoming_episodes:
        messages.append(f'<#{episode["channel_id"]}> episode **{episode["episode"]}** <t:{episode["airing"]}:R>')
    if len(messages) == 1:
        await ctx.send('Er zijn geen komende anime shows van posts die je volgt', ephemeral=True)
        return
    schedule_message = "\n".join(messages)
    if len(schedule_message) > 2000:
        await ctx.send(
            'Er zijn te veel shows om in 1 bericht weer te geven, '
            'gebruik day_offset om per dag te kijken, 0 is van nu tot binnen 24hrs, 1 is 24hrs verder etc',
            ephemeral=True)
        return
    await ctx.send(schedule_message, ephemeral=True)

async def setup(bot):
    bot.add_command(schedule)
