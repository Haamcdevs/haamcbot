import discord
from discord.ext import commands


class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _joinmessage(self, ctx, channel, category):
        pass

    @commands.command(pass_context=True)
    @commands.has_any_role("Shinsengumi", "Shinobi")
    async def animechannel(self, ctx, title, malurl):
        guild = ctx.message.guild
        category = None
        for cat in guild.categories:
            if cat.name == 'Anime':
                category = cat
        newchan = await guild.create_text_channel(
            name=title,
            category=category,
            topic=f'{title} || {malurl}',
            position=len(category.channels),
            reason=f"Aangevraagd door {ctx.author}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True)
            }
        )
        await ctx.message.delete()
        await newchan.send(f"Hallo iedereen! In deze channel kijken we naar **{title}**.\n{malurl}")


def setup(bot):
    bot.add_cog(Channels(bot))
