from discord.ext import commands
from discord.member import Member


@commands.hybrid_command(help='Leave a joinable channel', category='Channels')
async def leave(ctx):
    # Check that the user has a member read override
    user = ctx.message.author
    channel = ctx.message.channel
    await ctx.message.delete()
    is_joined = bool([
        o for o in channel.overwrites.items() if
        type(o[0]) is Member and o[0].id == user.id and o[1].read_messages is True
    ])
    if not is_joined:
        return
    # Remove the read override
    await channel.set_permissions(
        user,
        overwrite=None,
        reason=f"User left trough joinable channel"
    )
    await channel.send(f":outbox_tray: {user.mention} left")
    print(f'{user} left channel {channel} using the leave command')


async def setup(bot):
    bot.add_command(leave)
