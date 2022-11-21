import re

from discord import ForumTag
from discord.ext.commands import Context
from AnilistPython import Anilist

import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from util.html2md import html2md


class AnimeForm(Modal):
    def __init__(self, anime, anilist_link):
        self.name_preview = anime['name_english'] or anime['name_romaji']
        super().__init__(title=f'Create post for {self.name_preview}'[0:45])  # Modal title
        self.anime = anime
        #print(anime)
        self.anilist_link = anilist_link
        self.name = TextInput(label='name', required=True, default=self.name_preview[0:100])
        self.youtube = TextInput(label='Youtube trailer link', required=False)

        self.add_item(self.name)
        self.add_item(self.youtube)

    def filter_tags(self, tag: ForumTag):
        return tag.name in self.anime['genres']

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(config.channel["anime_forum"])
        description = html2md(self.anime['desc'])
        content = f'**description:** {description}\n**Start date:** {self.anime["starting_time"]}\n{self.anime["cover_image"]}\n<{self.anilist_link}>\n{self.youtube.value}'
        thread = await forum.create_thread(
            name=self.name.value,
            content=content,
            reason=f"Anime thread created by {interaction.user.name}"
        )
        tags = []
        filtered = filter(self.filter_tags, forum.available_tags)
        for tag in filtered:
            if len(tags) >= 5:
                break
            tags.append(tag)
        await thread[0].add_tags(*tags)
        await interaction.response.send_message(f'Created <#{thread[0].id}> in <#{forum.id}>')


@commands.hybrid_command(help='Create an anime post')
@commands.has_role(config.role['user'])
async def animepost(ctx: Context, anilist_link):
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
    bot.add_command(animepost)
