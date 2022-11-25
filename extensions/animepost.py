import re

from discord import ForumTag
from discord.ext.commands import Context
from anilist.shedule import AnilistSchedule

import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

from util.airing import Airing


class AnimeForm(Modal):
    def __init__(self, anime, anilist_link):
        super().__init__(title=f'Create post for {anime["name"]}'[0:45])  # Modal title
        self.anime = anime
        self.airing = Airing()
        self.anilist_link = anilist_link
        self.name = TextInput(label='name', required=True, default=anime['name'][0:100])
        self.add_item(self.name)
        self.youtube = TextInput(label='Youtube trailer link', required=False, default=self.anime['trailer'])
        if anime['trailer'] is None:
            self.add_item(self.youtube)

    def filter_tags(self, tag: ForumTag):
        return tag.name in self.anime['genres']

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(config.channel["anime_forum"])
        content = f'**Description:** {self.anime["description"]}\n**Start date:** {self.anime["starts_at"]}\n{self.anime["image"]}\n<{self.anilist_link}>'
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
        await thread.message.pin()
        # Add notifications
        if self.anime is not None:
            self.airing.add_notifications_to_channel(thread[0].id, interaction.guild_id, self.anime)
        # Add trailer
        if self.youtube.value != '':
            await thread[0].send(self.youtube.value)
        await interaction.response.send_message(f'Created <#{thread[0].id}> in <#{forum.id}>')


@commands.hybrid_command(help='Create an anime post')
@commands.has_role(config.role['user'])
async def anime_post(ctx: Context, anilist_link):
    try:
        anilist_id = re.search(r'anime/(\d+)', anilist_link)[1]
    except TypeError:
        await ctx.interaction.response.send_message(':x: Invalid anilist url', ephemeral=True)
        return
    anime = AnilistSchedule().get_anime_shedule_by_id(anilist_id)
    modal = AnimeForm(anime, anilist_link)
    await ctx.interaction.response.send_modal(modal)
    print(f'Created anime post for {modal.name} by {ctx.interaction.user.name}')


async def setup(bot):
    bot.add_command(anime_post)
