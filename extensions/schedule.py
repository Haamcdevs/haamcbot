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
    for episode in upcoming_episodes:
        if not user_in_channel(ctx, episode['channel_id']):
            continue
        messages.append(f'<#{episode["channel_id"]}> episode **{episode["episode"]}** <t:{episode["airing"]}:R>')
    if len(messages) == 1:
        await ctx.send('Er zijn geen komende anime shows van posts die je volgt', ephemeral=True)
        return
    await ctx.send("\n".join(messages), ephemeral=True)


def user_in_channel(ctx:Context, channelid: int):
    channel = ctx.guild.get_channel_or_thread(channelid)
    users = [
        user
        for user in channel.members
        if user.id == ctx.author.id
    ]
    return len(users) > 0


async def setup(bot):
    bot.add_command(schedule)
