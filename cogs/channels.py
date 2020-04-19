import discord
import re
import config
from discord.ext import commands
from discord.member import Member
from jikanpy import Jikan

jikan = Jikan()


class JoinableMessage():
    def __init__(self, message, bot):
        self.message = message
        self.bot = bot

    def is_joinable(self):
        if self.message.author.id != self.bot.user.id:
            return False
        if len(self.message.embeds) == 0:
            return False
        if self.get_field('channel') is None:
            return False
        return True

    def get_field(self, name):
        try:
            return next(field for field in self.message.embeds[0].fields if field.name == name)
        except StopIteration:
            return None

    def get_channel_id(self):
        return re.search(r'\d+', self.get_field('channel').value)[0]

    async def get_channel(self):
        return await self.bot.fetch_channel(self.get_channel_id())

    async def is_joined(self, user):
        channel = await self.get_channel()
        for ow in channel.overwrites.items():
            if type(ow[0]) is not Member:
                continue
            if ow[0].id != user.id:
                continue
            # Already in the channel
            if ow[1].read_messages is True:
                return True
            # Banned
            if ow[1].read_messages is False:
                return True
        return False

    async def add_user(self, user):
        channel = await self.get_channel()
        await channel.set_permissions(user, read_messages=True, reason=f"User joined trough joinable channel")
        await channel.send(f":inbox_tray: {user.mention} joined")


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
        welcomemsg = f"Hallo iedereen! In deze channel kijken we naar **{maldata['title']}**.\nMAL: {maldata['url']}"
        if trailer := maldata['trailer_url']:
            if 'embed' in trailer:
                trailer = f"https://www.youtube.com/watch?v={re.search('/embed/([^?]+)', trailer)[1]}"
            welcomemsg += f'\nTrailer: {trailer}'
        welcomemsg += f"\nMirai: `m.airing notify channel {maldata['title']}`"
        msg = await newchan.send(welcomemsg)
        await msg.pin()

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def join(self, payload):
        if payload.emoji.name != '▶':
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        user = await self.bot.fetch_user(payload.user_id)
        message = JoinableMessage(msg, self.bot)
        if message.is_joinable() is False:
            return
        await next(r for r in msg.reactions if r.emoji == '▶').remove(user)
        if await message.is_joined(user):
            return
        await message.add_user(user)


def setup(bot):
    bot.add_cog(Channels(bot))
