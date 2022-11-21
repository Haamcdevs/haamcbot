import sys
import time

from discord import ChannelType, TextStyle
from discord.ext.commands import Context

import config
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, ChannelSelect


class ChannelForm(Modal):
    def __init__(self):
        super().__init__(title="Create a new joinable channel")  # Modal title

        self.name = TextInput(label="Name")
        self.add_item(self.name)

        #self.category = ChannelSelect(channel_types=[])
        self.category = TextInput(label="Category id")
        self.add_item(self.category)

        self.description = TextInput(label="Description", style=TextStyle.long)
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(int(self.category.value))
        await interaction.response.send_message(f'Channel {self.name}, category: {category.name}, description {self.description}')


@commands.hybrid_command(help='Testing stuff')
@commands.has_role(config.role['global_mod'])
async def test(ctx: Context):
    modal = ChannelForm()
    await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(test)
