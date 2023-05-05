from pprint import pprint

from discord.errors import NotFound
from discord.ext import commands
from discord.ext.commands import Context


from util.airing import Airing


@commands.hybrid_command(help='Show anime schedule', category='Anime')
async def schedule(ctx: Context):
    airing = Airing()
    messages = ['Jou animerooster voor komende week']
    upcoming_episodes = airing.load_upcoming(24*7)
    if len(upcoming_episodes) == 0:
        await ctx.send('No episodes found in next week', ephemeral=True)
        return
    member = ctx.guild.get_member(ctx.author.id)
    for episode in upcoming_episodes:
        post = ctx.guild.get_channel_or_thread(episode["channel_id"])
        try:
            await post.fetch_member(ctx.author.id)
            messages.append(f'<#{episode["channel_id"]}> episode **{episode["episode"]}** <t:{episode["airing"]}:R>')
        except NotFound:
            continue
    await ctx.send("\n".join(messages), ephemeral=True)


async def setup(bot):
    bot.add_command(schedule)
