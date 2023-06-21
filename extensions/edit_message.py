import discord
from discord import Message
from discord.ui import Modal, TextInput

import config

from discord.ext import commands
from discord.ext.commands import Context


class EditMessageForm(Modal):
    def __init__(self, ctx: Context, message: Message):
        super().__init__(title='Edit bot message', timeout=None)  # Modal title
        self.ctx = ctx
        self.message = message
        self.content = TextInput(
            label='Content',
            required=True,
            default=self.message.content,
            custom_id='content',
            style=discord.TextStyle.long
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await self.message.edit(content=self.content.value)
        await interaction.response.send_message(f'Edited bot message {self.message.jump_url}', ephemeral=True)
        print(f'Rory message {self.message.jump_url} edited')


@commands.hybrid_command()
@commands.has_role(config.role['global_mod'])
async def edit_message(ctx: Context, message_id: str):
    message = await ctx.fetch_message(message_id)
    modal = EditMessageForm(ctx, message)
    await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(edit_message)
