import re

from discord import ForumTag
from discord.ext.commands import Context
from anilist.anime import AnimeClient

import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

from util.airing import Airing


class AnimeForm(Modal):
    def __init__(self, anime, anilist_link):
        super().__init__(title=f'Maak post aan voor {anime["name"]}'[0:45])  # Modal title
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
        first_episode = self.anime['starts_at']
        if len(self.anime['airdates']) and self.anime['airdates'][0]['episode'] == 1:
            first_episode = f"<t:{self.anime['airdates'][0]['time']}:R>"
        content = f'**Description:** {self.anime["description"]}\n' \
                  f'**First epidsode:** {first_episode}\n' \
                  f'{self.anime["image"]}\n' \
                  f'<{self.anilist_link}>\n' \
                  f'{self.youtube.value}'
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
        self.airing.add_notifications_to_channel(thread[0].id, interaction.guild_id, self.anime)
        await interaction.response.send_message(f'Anime post <#{thread[0].id}> aangemaakt in <#{forum.id}>')


@commands.hybrid_command(help='Create an anime post')
@commands.has_role(config.role['user'])
async def anime_post(ctx: Context, anilist_link):
    try:
        anilist_id = re.search(r'anime/(\d+)', anilist_link)[1]
    except TypeError:
        await ctx.send(':x: Invalid anilist url', ephemeral=True)
        return
    anime = AnimeClient().by_id(anilist_id)
    modal = AnimeForm(anime, anilist_link)
    await ctx.interaction.response.send_modal(modal)
    print(f'Created anime post for {modal.name} by {ctx.interaction.user.name}')


async def setup(bot):
    bot.add_command(anime_post)
