import discord
import re
from discord.ext import commands
from jikanpy import Jikan

jikan = Jikan()


class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _getmaldata(url):
        # Using regex to get MAL id out of URL (easier to use with Jikan)
        mal_id = re.search('\d+', url)
        anime = jikan.anime(mal_id[0])
        return anime

    @staticmethod
    async def _joinmessage(channel, categorychannel, malurl):
        maldata = Channels._getmaldata(malurl)
        embed = discord.Embed(
            title=maldata['title'],
            type='rich',
            url=malurl
        )
        # embed.set_author(name=maldata['title'], icon_url='', url=malurl)
        embed.set_footer(text='Druk op de reactions om te joinen / leaven')
        embed.set_thumbnail(url=maldata['image_url'])
        embed.add_field(name='studio', value=', '.join([stu['name'] for stu in maldata['studios']]))
        embed.add_field(name='datum', value=maldata['aired']['string'])
        embed.add_field(name='genres', value=', '.join([gen['name'] for gen in maldata['genres']]))
        embed.add_field(name='channel', value=channel.mention)
        embed.add_field(name='kijkers', value=len(channel.members)-1)
        msg = await categorychannel.send(embed=embed)
        await msg.add_reaction('▶')
        await msg.add_reaction('⏹')

    @commands.command(pass_context=True)
    @commands.has_any_role("Shinsengumi", "Shinobi", "Anime Mod")
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
        for cat in guild.categories:
            if 'joinable-channels' in cat.name:
                for chan in cat.channels:
                    if 'anime' in chan.name:
                        categorychannel = chan
        await self._joinmessage(newchan, categorychannel, malurl)
        await ctx.message.delete()
        await newchan.send(f"Hallo iedereen! In deze channel kijken we naar **{title}**.\n{malurl}")


def setup(bot):
    bot.add_cog(Channels(bot))
