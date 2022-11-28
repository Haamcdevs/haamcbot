import asyncio

from discord import Member
from discord.ext import commands

import config
from discord.ext.commands import Cog, Context


class JoinMessage(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='welcome')
    async def welcome(self, ctx):
        return

    @Cog.listener()
    async def on_member_join(self, member: Member):
        channel = member.guild.get_channel_or_thread(config.channel['welcome'])
        await self.send_welcome(channel, member)

    # @welcome.command()
    # async def test(self, ctx: Context):
    #     member = ctx.author
    #     channel = ctx.guild.get_channel_or_thread(config.channel['welcome'])
    #     await self.send_welcome(channel, member)
    #     await ctx.send('done', ephemeral=True)

    async def send_welcome(self, channel, member):
        await asyncio.sleep(3)
        await channel.send(
            f'Welkom {member.mention}, ik ben Rory, de mascotte van {member.guild.name}!\n'
            f'Voor toegang tot de server hebben we nog enkele vragen. \n\n'
            f':one: Wat is je **favoriete serie**?\n\n'
            f':two: **Hoe of waar** heb je ons gevonden?'
        )


async def setup(bot):
    await bot.add_cog(JoinMessage(bot))
