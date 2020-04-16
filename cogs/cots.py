import config
from discord.ext import commands


class Cots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def set_season(season: str):
        fd = open('./var/cots_season', 'w')
        fd.write(season)
        fd.close()

    @staticmethod
    def get_season():
        fd = open('./var/cots_season', 'r')
        season = fd.read()
        fd.close()
        return season

    @commands.group(name='cots')
    @commands.has_role(config.role_global_mod)
    async def start(self, ctx, cmd, season: str, year: str):
        user = ctx.message.author
        channel = next(ch for ch in user.guild.channels if ch.id == config.cots_channel)
        role = next(r for r in user.guild.roles if r.id == config.role_user)
        season = f'{season} {year}'
        self.set_season(season)
        await channel.send(f"Bij deze zijn de nominaties voor season {season} geopend!")
        await channel.set_permissions(role, send_messages=True, reason=f'Starting cots, triggered by {user.name}')


def setup(bot):
    bot.add_cog(Cots(bot))
