import re

import discord
import mysql
from discord.ext import tasks, commands
from discord.ext.commands import Context, Bot

from anilist.anime import AnimeClient

import config
from util.airing import Airing


class Notifications(commands.Cog):
    def __init__(self, ctx: Bot):
        self.ctx: Bot = ctx
        self.airing = Airing()

    async def cog_load(self):
        self.notify_anime_channel.start()
        self.reconnect_db.start()

    @commands.hybrid_group(name='airing', invoke_without_commands=False, help='Anime Notifications')
    async def airing(self, ctx):
        return

    async def by_name(self, ctx: Context, name: str):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        anime = await AnimeClient().by_title(name)
        if anime is None:
            await ctx.send(f':x: Anime {name} not found', ephemeral=True)
            return
        self.airing.add_notifications_to_channel(channel_id, guild_id, anime)
        episode_count = len(anime.airdates)
        anime_name = anime.name
        await ctx.send(f'Added {episode_count} airing notifications for {anime_name}')

    @airing.command(pass_context=True, description='Toon de wanneer de volgende episode aired.')
    @commands.has_role(config.role['user'])
    async def next(self, ctx: Context):
        channel_id = ctx.channel.id
        notifications = list(Airing().load_next(channel_id))
        if len(notifications) == 0:
            await ctx.send(f'Geen volgende aflevering gevonden voor dit kanaal', ephemeral=True)
            return
        notification = notifications[0]
        name = notification['anime_name'].decode('utf-8')
        await ctx.send(f"Aflevering **{notification['episode']}** van **{name}** komt uit <t:{notification['airing']}:R>.")

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @airing.command(pass_context=True)
    async def add(self, ctx: Context, anilist_link: str):
        try:
            anime_id = re.search(r'anime/(\d+)', anilist_link)[1]
        except TypeError:
            await ctx.send(':x: Invalid anilist url', ephemeral=True)
            return
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        anime = await AnimeClient().by_id(anime_id)
        if anime is None:
            await ctx.send(f':x: Anime {anime_id} not found', ephemeral=True)
            return
        self.airing.add_notifications_to_channel(channel_id, guild_id, anime)
        episode_count = len(anime.airdates)
        anime_name = anime.name
        await ctx.send(f'Added **{episode_count}** upcoming airing notifications for **{anime_name}**', ephemeral=True)

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @airing.command(pass_context=True)
    async def clear(self, ctx: Context):
        self.airing.clear_channel(ctx.channel.id)
        await ctx.send(f'Cleared all channel anime airing notifications', ephemeral=True)

    @tasks.loop(seconds=60)
    async def notify_anime_channel(self):
        if not self.ctx.is_ready():
            print('anime notification: Context not ready')
            return
        # Update the anime schedule
        for notification in await self.load_notifications():
            await self.refresh_schedule(notification)
        # Re-fetch notifications after update
        last_sent = None
        for notification in await self.load_notifications():
            name = await self.send_notification(notification)
            if name is not None:
                last_sent = (name, notification['episode'])
        if last_sent is None:
            return
        try:
            activity = discord.Activity(name='anime', state=f'{last_sent[0]} ep. {last_sent[1]}', type=discord.ActivityType.watching)
            await self.ctx.change_presence(status=discord.Status.online, activity=activity)
        except Exception as e:
            print(f'anime notification: Failed to set watching status: {e}')

    async def load_notifications(self):
        try:
            return self.airing.load_current_notifications()
        except mysql.connector.errors.DatabaseError:
            print('anime notification: Db connection failed')
            await self.reconnect_db()
            return []

    async def refresh_schedule(self, notification):
        # A single anime that AniList or Discord chokes on may not stop the rest of the schedule.
        try:
            anime = await AnimeClient().by_id(notification['anime_id'])
            if anime is None:
                print(f"Failed loading anime schedule for anime with id (AniList fucked up) {notification['anime_id']}")
                return
            guild = self.ctx.get_guild(notification['guild_id'])
            if guild is None:
                print(f"anime notification: Guild {notification['guild_id']} unavailable")
                return
            if guild.get_channel_or_thread(notification['channel_id']) is None:
                self.airing.clear_channel(notification['channel_id'])
                return
            print(f"anime notification: Updating anime schedule {notification['anime_id']}")
            self.airing.add_notifications_to_channel(notification['channel_id'], notification['guild_id'], anime)
        except Exception as e:
            print(f"anime notification: Updating schedule for {notification['anime_id']} failed: {e}")

    async def send_notification(self, notification):
        """Post one episode notification. Returns the anime name when it went out, None when it did not."""
        name = None
        try:
            name = await self.post_episode(notification)
        except Exception as e:
            print(f"anime notification: Sending notification {notification['id']} failed: {e}")
        try:
            self.airing.remove_notification(notification['id'])
        except Exception as e:
            print(f"anime notification: Removing notification {notification['id']} failed: {e}")
        return name

    async def post_episode(self, notification):
        guild = self.ctx.get_guild(notification['guild_id'])
        channel = guild.get_channel_or_thread(notification['channel_id']) if guild is not None else None
        if channel is None:
            return None
        name = notification['anime_name'].decode('utf-8')
        anime_post = await channel.send(f"Aflevering **{notification['episode']}** van **{name}** is uit sinds <t:{notification['airing']}:R>.\nWat vind jij van deze aflevering?")
        for reaction in ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'):
            await anime_post.add_reaction(reaction)
        print(f"anime notification: Episode **{notification['episode']}** of **{name}** airing notification sent")
        return name


    @tasks.loop(hours=24)
    async def reconnect_db(self):
        print('anime notification: Reconnecting airing database')
        self.airing.reconnect()


async def setup(bot):
    await bot.add_cog(Notifications(bot))
