from asyncio import Task

import pytz
from discord.ext import tasks, commands
from discord.ext.commands import Context, Bot
from datetime import datetime, time

from anilist.shedule import AnilistSchedule
import mysql.connector

import config

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)


class Notifications(commands.Cog):
    def __init__(self, ctx: Bot):
        self.ctx: Bot = ctx
        self.cursor = database.cursor(dictionary=True)

    async def cog_load(self):
        self.notify_anime_channel.start()

    def load_current_notifications(self):
        check_time = datetime.timestamp(datetime.now())
        sql = f'SELECT * FROM anime_notifications WHERE airing < {check_time}'
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def remove_notification(self, notification_id: int):
        sql = f'DELETE FROM anime_notifications WHERE id = {notification_id}'
        self.cursor.execute(sql)
        database.commit()

    def store_notification(self, anime_id, episode, guild_id, channel_id, anime_name, airing):
        sql = "INSERT INTO anime_notifications (anime_id, episode, guild_id, channel_id, anime_name, airing)" \
              " VALUES (%s, %s, %s, %s, %s, %s)" \
              "ON DUPLICATE KEY UPDATE airing=%s"
        val = (anime_id, episode, guild_id, channel_id, anime_name, airing, airing)
        # Execute SQL
        self.cursor.execute(sql, val)
        database.commit()

        # Commit change
        database.commit()

    def clear_channel(self, channel_id):
        sql = f'DELETE FROM anime_notifications WHERE channel_id = {channel_id}'
        self.cursor.execute(sql)
        database.commit()

    @commands.hybrid_group(name='notification', invoke_without_commands=False, help='Anime Notifications')
    async def notify(self, ctx):
        return

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @notify.command(pass_context=True)
    async def add_name(self, ctx: Context, name: str):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        response = AnilistSchedule.get_anime_shedule_by_title(name)
        if response['data'] is None or response['data']['Media'] is None:
            await ctx.interaction.response.send_message(f':x: Anime {name} not found', ephemeral=True)
            return
        await self.add_notifications_to_channel(channel_id, guild_id, response)
        episode_count = len(response['data']['Media']['airingSchedule']['edges'])
        anime_name = response['data']['Media']['title']['romaji']
        await ctx.interaction.response.send_message(f'Added {episode_count} airing notifications for {anime_name}')

    async def add_notifications_to_channel(self, channel_id, guild_id, response):
        anime_id = response['data']['Media']['id']
        anime_name = response['data']['Media']['title']['romaji']
        schedule = response['data']['Media']['airingSchedule']['edges']
        for episode in schedule:
            self.store_notification(
                anime_id,
                episode['node']['episode'],
                guild_id,
                channel_id,
                anime_name,
                episode['node']['airingAt']
            )

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @notify.command(pass_context=True)
    async def add_id(self, ctx: Context, anime_id: int):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        response = AnilistSchedule.get_anime_shedule_by_id(anime_id)
        if response['data'] is None or response['data']['Media'] is None:
            await ctx.interaction.response.send_message(f':x: Anime {anime_id} not found', ephemeral=True)
            return
        await self.add_notifications_to_channel(channel_id, guild_id, response)
        episode_count = len(response['data']['Media']['airingSchedule']['edges'])
        anime_name = response['data']['Media']['title']['romaji']
        await ctx.interaction.response.send_message(f'Added {episode_count} airing notifications for {anime_name}')

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @notify.command(pass_context=True)
    async def clear(self, ctx: Context):
        self.clear_channel(ctx.channel.id)
        await ctx.interaction.response.send_message(f'Cleared all channel anime airing notifications')

    @tasks.loop(seconds=10)
    async def notify_anime_channel(self):
        if not self.ctx.is_ready():
            return
        print('notify_anime_channel.notify')
        for notification in self.load_current_notifications():
            response = AnilistSchedule.get_anime_shedule_by_id(notification['anime_id'])
            if response['data'] is not None and response['data']['Media'] is not None:
                guild = self.ctx.get_guild(notification['guild_id'])
                if guild.get_channel_or_thread(notification['channel_id']) is None:
                    continue
                print(f"Updating anime schedule f{notification['anime_id']}")
                await self.add_notifications_to_channel(notification['channel_id'], notification['guild_id'], response)

        for notification in self.load_current_notifications():
            guild = self.ctx.get_guild(notification['guild_id'])
            channel = guild.get_channel_or_thread(notification['channel_id'])
            if channel is not None:
                await channel.send(f"Episode **{notification['episode']}** of **{notification['anime_name']}** aired <t:{notification['airing']}:R>.")
            self.remove_notification(notification['id'])
            print(f"Episode **{notification['episode']}** of **{notification['anime_name']}** airing notification sent")


async def setup(bot):
    await bot.add_cog(Notifications(bot))
