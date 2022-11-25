import re

import mysql.connector
from discord import ForumTag
from discord.ext.commands import Context
from AnilistPython import Anilist
from anilist.shedule import AnilistSchedule


import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from util.html2md import html2md


database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)

class AnimeForm(Modal):
    def __init__(self, anime, anilist_link):
        self.name_preview = anime['name_english'] or anime['name_romaji']
        super().__init__(title=f'Create post for {self.name_preview}'[0:45])  # Modal title
        self.anime = anime
        #print(anime)
        self.anilist_link = anilist_link
        self.name = TextInput(label='name', required=True, default=self.name_preview[0:100])
        #self.youtube = TextInput(label='Youtube trailer link', required=False)
        self.cursor = database.cursor(dictionary=True)
        self.add_item(self.name)
        #self.add_item(self.youtube)

    def filter_tags(self, tag: ForumTag):
        return tag.name in self.anime['genres']

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(config.channel["anime_forum"])
        description = html2md(self.anime['desc'])
        content = f'**description:** {description}\n**Start date:** {self.anime["starting_time"]}\n{self.anime["cover_image"]}\n<{self.anilist_link}>'
        tags = []
        filtered = filter(self.filter_tags, forum.available_tags)
        for tag in filtered:
            if len(tags) >= 5:
                break
            tags.append(tag)
        thread = await forum.create_thread(
            name=self.name.value,
            content=content,
            reason=f"Anime thread created by {interaction.user.name}",
            applied_tags=tags
        )
        response = AnilistSchedule.get_anime_shedule_by_title(self.name_preview)
        if response['data'] is not None and response['data']['Media'] is not None:
            await self.add_notifications_to_channel(thread[0].id, interaction.guild_id, response)
        if response['data']['Media']['trailer'] is not None:
            await thread[0].send(f"https://www.youtube.com/watch?v={response['data']['Media']['trailer']['id']}")
        await interaction.response.send_message(f'Created <#{thread[0].id}> in <#{forum.id}>')

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

    def store_notification(self, anime_id, episode, guild_id, channel_id, anime_name, airing):
        sql = "INSERT INTO anime_notifications (anime_id, episode, guild_id, channel_id, anime_name, airing)" \
              " VALUES (%s, %s, %s, %s, %s, %s)" \
              "ON DUPLICATE KEY UPDATE airing=airing"
        val = (anime_id, episode, guild_id, channel_id, anime_name, airing)
        # Execute SQL
        self.cursor.execute(sql, val)
        database.commit()

        # Commit change
        database.commit()


@commands.hybrid_command(help='Create an anime post')
@commands.has_role(config.role['user'])
async def anime_post(ctx: Context, anilist_link):
    try:
        anilist_id = re.search(r'anime/(\d+)', anilist_link)[1]
    except TypeError:
        await ctx.interaction.response.send_message(':x: Invalid anilist url', ephemeral=True)
        return
    anilist = Anilist()
    anime = anilist.get_anime_with_id(anilist_id)
    modal = AnimeForm(anime, anilist_link)
    await ctx.interaction.response.send_modal(modal)
    print(f'Created anime post for {modal.name} by {ctx.interaction.user.name}')


async def setup(bot):
    bot.add_command(anime_post)
