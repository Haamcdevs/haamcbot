import config
from discord.ext import commands


class Cots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, name='cots start')
    @commands.has_role(config.role_global_mod)
    async def start(self, ctx, *, member):
        channel = next(ch for ch in member.guild.channels if ch.id == config.cots_channel)
        role = next(r for r in member.guild.roles if r.id == config.role_user)
        await channel.send(f"Bij deze zijn de nominaties voor season {config.cots_season} geopend!")
        await channel.set_permissions(role, send_messages=True)


def setup(bot):
    bot.add_cog(Cots(bot))
