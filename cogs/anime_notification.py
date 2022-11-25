import re
from discord.ext import tasks, commands
from discord.ext.commands import Context, Bot

from anilist.shedule import AnilistSchedule

import config
from util.airing import Airing


class Notifications(commands.Cog):
    def __init__(self, ctx: Bot):
        self.ctx: Bot = ctx
        self.airing = Airing()

    async def cog_load(self):
        self.notify_anime_channel.start()

    @commands.hybrid_group(name='airing', invoke_without_commands=False, help='Anime Notifications')
    async def airing(self, ctx):
        return

    async def by_name(self, ctx: Context, name: str):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        anime = AnilistSchedule().get_anime_shedule_by_title(name)
        if anime is None:
            await ctx.interaction.response.send_message(f':x: Anime {name} not found', ephemeral=True)
            return
        self.airing.add_notifications_to_channel(channel_id, guild_id, anime)
        episode_count = len(anime['airdates'])
        anime_name = anime['name']
        await ctx.interaction.response.send_message(f'Added {episode_count} airing notifications for {anime_name}')

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @airing.command(pass_context=True)
    async def add(self, ctx: Context, anilist_link: str):
        try:
            anime_id = re.search(r'anime/(\d+)', anilist_link)[1]
        except TypeError:
            await ctx.interaction.response.send_message(':x: Invalid anilist url', ephemeral=True)
            return
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id
        anime = AnilistSchedule().get_anime_shedule_by_id(anime_id)
        if anime is None:
            await ctx.interaction.response.send_message(f':x: Anime {anime_id} not found', ephemeral=True)
            return
        self.airing.add_notifications_to_channel(channel_id, guild_id, anime)
        episode_count = len(anime['airdates'])
        anime_name = anime['name']
        await ctx.interaction.response.send_message(f'Added **{episode_count}** upcoming airing notifications for **{anime_name}**')

    @commands.has_role(config.role['global_mod'])
    @commands.has_role(config.role['anime_mod'])
    @airing.command(pass_context=True)
    async def clear(self, ctx: Context):
        self.airing.clear_channel(ctx.channel.id)
        await ctx.interaction.response.send_message(f'Cleared all channel anime airing notifications')

    @tasks.loop(seconds=10)
    async def notify_anime_channel(self):
        if not self.ctx.is_ready():
            return
        # Update the anime schedule
        for notification in self.airing.load_current_notifications():
            anime = AnilistSchedule().get_anime_shedule_by_id(notification['anime_id'])
            if anime is not None:
                guild = self.ctx.get_guild(notification['guild_id'])
                if guild.get_channel_or_thread(notification['channel_id']) is None:
                    continue
                print(f"Updating anime schedule {notification['anime_id']}")
                self.airing.add_notifications_to_channel(notification['channel_id'], notification['guild_id'], anime)
        # Re-fetch notifications after update
        for notification in self.airing.load_current_notifications():
            guild = self.ctx.get_guild(notification['guild_id'])
            channel = guild.get_channel_or_thread(notification['channel_id'])
            if channel is not None:
                await channel.send(f"Episode **{notification['episode']}** of **{notification['anime_name']}** aired <t:{notification['airing']}:R>.")
                print(f"Episode **{notification['episode']}** of **{notification['anime_name']}** airing notification sent")
            self.airing.remove_notification(notification['id'])

async def setup(bot):
    await bot.add_cog(Notifications(bot))
