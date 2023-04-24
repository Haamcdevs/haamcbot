from discord.ext import commands
from discord.ext.commands import Context


from util.airing import Airing


@commands.hybrid_command(help='Show upcoming airing shows that have a anime post', category='Anime')
async def upcoming(ctx: Context):
    airing = Airing()
    messages = ['Upcoming episodes in the next 24 hours']
    upcoming_episodes = airing.load_upcoming(24)
    if len(upcoming_episodes) == 0:
        await ctx.send('No episodes found in next 24 hours', ephemeral=True)
        return
    for episode in upcoming_episodes:
        messages.append(f'<#{episode["channel_id"]}> episode **{episode["episode"]}** airs <t:{episode["airing"]}:R>')
    await ctx.send("\n".join(messages))


async def setup(bot):
    bot.add_command(upcoming)
