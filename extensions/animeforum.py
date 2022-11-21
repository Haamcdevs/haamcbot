import re

from discord import ChannelType, TextStyle, ForumChannel, ForumTag
from discord.ext.commands import Context
from AnilistPython import Anilist

import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, ChannelSelect


class AnimeForm(Modal):
    def __init__(self, anime, anilist_link):
        self.name_preview = anime['name_english'] or anime['name_romaji']
        super().__init__(title=f'Create post for {self.name_preview}'[0:45])  # Modal title
        self.anime = anime
        #print(anime)
        self.anilist_link = anilist_link
        self.name = TextInput(label='name', placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ", required=True, default=self.name_preview[0:100])
        self.youtube = TextInput(label='Youtube trailer link', placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ", required=False)

        self.add_item(self.name)
        self.add_item(self.youtube)

    def filter_tags(self, tag: ForumTag):
        return tag.name in self.anime['genres']

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(config.channel["anime_forum"])
        description = self.anime['desc'].replace('<br>', "\n")\
            .replace('<b>', '**')\
            .replace('</b>', '**')\
            .replace('<i>', '*')\
            .replace('</i>', '*')

        content = f'**description:** {description}\n**Start date:** {self.anime["starting_time"]}\n{self.anime["cover_image"]}\n<{self.anilist_link}>\n{self.youtube.value}'
        thread = await forum.create_thread(
            name=self.name.value,
            content=content,
            reason=f"Anime thread created by {interaction.user.name}"
        )
        tags = []
        filtered = filter(self.filter_tags, forum.available_tags)
        for tag in filtered:
            tags.append(tag)
        await thread[0].add_tags(*tags)
        await interaction.response.send_message(f'Created <#{thread[0].id}> in <#{forum.id}>')


@commands.hybrid_command(help='Create an anime post')
@commands.has_role(config.role['global_mod'])
async def animepost(ctx: Context, anilist_link):
    anilist_id = re.search(r'anime/(\d+)', anilist_link)[1]
    anilist = Anilist()
    anime = anilist.get_anime_with_id(anilist_id)
    modal = AnimeForm(anime, anilist_link)
    await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(animepost)
