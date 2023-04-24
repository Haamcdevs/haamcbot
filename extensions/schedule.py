from discord.ext import commands
from discord.ext.commands import Context


from util.airing import Airing


@commands.hybrid_command(help='Show anime schedule', category='Anime')
async def schedule(ctx: Context):
    airing = Airing()
    messages = ['Animerooster voor komende week']
    upcoming_episodes = airing.load_upcoming(24*7)
    if len(upcoming_episodes) == 0:
        await ctx.send('No episodes found in next week', ephemeral=True)
        return
    for episode in upcoming_episodes:
        messages.append(f'<#{episode["channel_id"]}> episode **{episode["episode"]}** <t:{episode["airing"]}:R>')
    await ctx.send("\n".join(messages))


async def setup(bot):
    bot.add_command(schedule)
