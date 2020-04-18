import discord
import re
import config
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
    async def _joinmessage(channel, categorychannel, maldata):
        # Maybe rewrite so its not limited to anime?
        embed = discord.Embed(
            type='rich',
        )
        embed.set_author(name=maldata['title'], icon_url='https://i.imgur.com/pcdrHvS.png', url=maldata['url'])
        embed.set_footer(text='Druk op de reactions om te joinen / leaven')
        embed.set_thumbnail(url=maldata['image_url'])
        embed.add_field(name='studio', value=', '.join([stu['name'] for stu in maldata['studios']]))
        embed.add_field(name='datum', value=maldata['aired']['string'])
        embed.add_field(name='genres'.ljust(122) + "ᅠ",
                        value=', '.join([gen['name'] for gen in maldata['genres']]),
                        inline=False)
        embed.add_field(name='channel', value=channel.mention)
        # When created, value is 0. Amount increased when someone joins/leaves.
        embed.add_field(name='kijkers', value=0)
        msg = await categorychannel.send(embed=embed)
        await msg.add_reaction('▶')
        await msg.add_reaction('⏹')

    @commands.command(pass_context=True)
    @commands.has_any_role(config.role['global_mod'], config.role['anime_mod'])
    async def animechannel(self, ctx, title, malurl):
        guild = ctx.message.guild
        category = next(cat for cat in guild.categories if cat.id == config.category['anime'])
        # Get maldata here because we need it for the title
        maldata = Channels._getmaldata(malurl)
        newchan = await guild.create_text_channel(
            name=title,
            category=category,
            topic=f"{maldata['title']} || {maldata['url']}",
            position=len(category.channels),
            reason=f"Aangevraagd door {ctx.author}",
            overwrites=category.overwrites
        )
        categorychannel = next(chan for chan in guild.channels if chan.id == config.channel['join-anime'])
        await self._joinmessage(newchan, categorychannel, maldata)
        await ctx.message.delete()
        await newchan.send(f"Hallo iedereen! In deze channel kijken we naar **{title}**.\n{maldata['url']}")
        if trailer := maldata['trailer_url']:
            if 'embed' in trailer:
                trailer = f"https://www.youtube.com/watch?v={re.search('/embed/([^?]+)', trailer)[1]}"
            await newchan.send(trailer)
        await newchan.send(f"m.airing notify channel {maldata['title']}")


def setup(bot):
    bot.add_cog(Channels(bot))
