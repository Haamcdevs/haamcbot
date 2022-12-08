import re
from typing import List

import requests

import discord
from discord import ChannelType, ui, ButtonStyle, Interaction
from discord.app_commands import Choice
from discord.ext import commands
from discord.member import Member
from jikanpy import Jikan
from cachecontrol import CacheControl
from cachecontrol.heuristics import ExpiresAfter
from cachecontrol.caches.file_cache import FileCache
from discord.ext.commands import Context
from discord.ui import Modal, TextInput
from discord import ChannelType, TextStyle

import config

expires = ExpiresAfter(days=1)
session = CacheControl(requests.Session(), heuristic=expires, cache=FileCache(config.cache_dir))
jikan = Jikan(session=session)


class ChannelForm(Modal):
    def __init__(self, category_id: int, channels):
        super().__init__(title="Welcome to Create-a-channel", custom_id="create_form", timeout=None)  # Modal title
        self.category_id = category_id
        self.channels = channels
        self.name = TextInput(label="Name", min_length=2, max_length=32, custom_id="name")
        self.add_item(self.name)

        self.description = TextInput(label="Description", style=TextStyle.long, max_length=1024, required=False,
                                     custom_id="description")
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            category = next(cat for cat in interaction.guild.categories if cat.id == int(self.category_id))
        except StopIteration:
            await interaction.response.send_message(f':x: Cant find category <#{self.category_id}> :thinking:')
            return
        new_channel = await interaction.guild.create_text_channel(
            name=self.name.value,
            category=category,
            topic=self.description.value,
            position=len(category.channels),
            reason=f"Aangevraagd door {interaction.user}",
            overwrites=Channels.get_overwites(interaction.guild, category)
        )
        embed = JoinableMessage.create_simple_embed(new_channel, 0)
        await self.channels._joinmessage(interaction.channel, embed)
        await interaction.response.send_message(f'Joinable channel <#{new_channel.id}> created', ephemeral=True, delete_after=5)


class JoinableMessage:
    def __init__(self, message: discord.message, bot):
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

    async def get_channel(self) -> discord.channel:
        return await self.bot.fetch_channel(self.get_channel_id())

    async def is_joined(self, user: discord.user):
        channel = await self.get_channel()
        return bool([
            o for o in channel.overwrites.items() if
            type(o[0]) is Member and o[0].id == user.id and o[1].read_messages is True
        ])

    async def is_banned(self, user: discord.user):
        channel = await self.get_channel()
        return bool([
            o for o in channel.overwrites.items() if
            type(o[0]) is Member and o[0].id == user.id and o[1].read_messages is False
        ])

    async def get_member_count(self):
        channel = await self.get_channel()
        return len([
            o for o in channel.overwrites.items()
            if type(o[0]) is Member and o[1].read_messages is True and o[0].bot is False
        ])

    async def is_locked(self):
        message = await self.message.fetch()
        try:
            next(r for r in message.reactions if r.emoji == '🔒')
        except StopIteration:
            return False
        return True

    async def add_user(self, user: discord.user):
        channel = await self.get_channel()
        await channel.set_permissions(user, read_messages=True, reason=f"User joined trough joinable channel")
        await channel.send(f":inbox_tray: {user.mention} joined")
        await self.update_members()
        print(f'user {user} joined {channel.name}')

    async def remove_user(self, user: discord.user):
        channel = await self.get_channel()
        await channel.set_permissions(user, overwrite=None, reason=f"User left trough joinable channel")
        await channel.send(f":outbox_tray: {user.mention} left")
        await self.update_members()
        print(f'user {user} left {channel.name}')

    @staticmethod
    def create_simple_embed(channel: discord.TextChannel, members) -> discord.Embed:
        embed = discord.Embed(type='rich')
        embed.set_author(icon_url='https://i.imgur.com/pcdrHvS.png', name="")
        embed.add_field(name='description'.ljust(122) + "ᅠ", value=channel.topic, inline=False)
        embed.add_field(name='channel', value=channel.mention)
        embed.add_field(name='members', value=f'** ` {members} ` **')
        return embed

    async def update_members(self):
        member_count = await self.get_member_count()
        channel = await self.get_channel()
        embed = self.create_simple_embed(channel, member_count)
        await self.message.edit(embed=embed, view=self.bot.persistent_views[0])


class Channels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_roles = [config.role['global_mod'], config.role['anime_mod']]

    @staticmethod
    def get_overwites(guild: discord.guild, category: discord.CategoryChannel):
        overwrites = category.overwrites
        overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False)
        return overwrites

    async def _joinmessage(self, channel, embed) -> discord.message:
        return await channel.send(embed=embed, view=self.bot.persistent_views[0])

    @commands.hybrid_command(pass_context=True, help='Create a joinable channel')
    @commands.has_role(config.role['global_mod'])
    async def joinable_channel(self, ctx: Context, category):
        category_id = int(category)
        modal = ChannelForm(category_id, self)
        await ctx.interaction.response.send_modal(modal)

    @joinable_channel.autocomplete('category')
    async def category_autocomplete(self, ctx: Context, current: str) -> List[Choice[str]]:
        return [
            Choice(name=category.name, value=f'{category.id}')
            for category in ctx.guild.categories
            if category.type == ChannelType.category and category.name.lower().__contains__(current.lower())
        ]

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def join(self, payload):
        if payload.emoji.name != '▶' or payload.member.bot:
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        user = await self.bot.fetch_user(payload.user_id)
        message = JoinableMessage(msg, self.bot)
        if message.is_joinable() is False:
            return
        await next(r for r in msg.reactions if r.emoji == '▶').remove(user)
        joinable_channel = await message.get_channel()
        if await message.is_joined(user) or await message.is_banned(user):
            print(f'user {user} has already joined / is banned from {joinable_channel}')
            return
        await message.add_user(user)

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def leave(self, payload):
        if payload.emoji.name != '⏹' or payload.member.bot:
            return
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        user = await self.bot.fetch_user(payload.user_id)
        message = JoinableMessage(msg, self.bot)
        if message.is_joinable() is False:
            return
        await next(r for r in msg.reactions if r.emoji == '⏹').remove(user)
        if not await message.is_joined(user) or await message.is_banned(user):
            return
        await message.remove_user(user)
        joinable_channel = await message.get_channel()

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def refresh(self, payload):
        if payload.emoji.name != '🔁' or not bool([r for r in payload.member.roles if r.id in self.allowed_roles]):
            return
        user = await self.bot.fetch_user(payload.user_id)
        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        message = JoinableMessage(msg, self.bot)
        if message.is_joinable() is False:
            return
            return
        await msg.clear_reactions()
        await message.update_members()
        joinable_channel = await message.get_channel()
        print(f'user {user} updated {joinable_channel}')

    @commands.Cog.listener(name='on_raw_reaction_add')
    async def delete(self, payload):
        if payload.emoji.name != '🚮' or not bool([r for r in payload.member.roles if r.id in self.allowed_roles]):
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        message = JoinableMessage(msg, self.bot)
        if message.is_joinable() is False:
            return
        joinable_channel = await message.get_channel()
        await joinable_channel.delete()
        await msg.delete()
        print(f'user {payload.member} deleted {joinable_channel}')

    @commands.Cog.listener(name='on_click')
    async def on_button_click(interaction: Interaction):
        print(interaction.component)

    @commands.hybrid_command(pass_context=True, help='Restore a simple channel join message')
    @commands.has_role(config.role['global_mod'])
    async def rechannel(self, ctx, channelid):
        channel = await self.bot.fetch_channel(channelid)
        embed = JoinableMessage.create_simple_embed(channel, 0)
        message = await self._joinmessage(channel=ctx.channel, embed=embed)
        message = JoinableMessage(message, self.bot)
        await message.update_members()
        print(f'user {ctx.author} restored {channel}')
        await ctx.send('Done', ephemeral=True, delete_after=3)


async def setup(bot):
    await bot.add_cog(Channels(bot))
