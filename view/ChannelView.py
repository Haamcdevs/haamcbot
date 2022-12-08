import discord
from discord import ui, ButtonStyle

from cogs.channels import JoinableMessage


class ChannelView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(label="Join", style=ButtonStyle.green, custom_id='join')
    async def join_button(self, interaction: discord.Interaction, button: ui.Button):
        jm = JoinableMessage(interaction.message, self.bot)
        if await jm.is_joined(interaction.user):
            await interaction.response.send_message(f':x: You already joined', ephemeral=True, delete_after=2)
            return
        if await jm.is_locked():
            await interaction.response.send_message(f'🔒 Cannot join because the channel is locked', ephemeral=True, delete_after=2)
            return
        await jm.add_user(interaction.user)
        await interaction.response.send_message(f'You joined channel <#{jm.get_channel_id()}>', ephemeral=True,
                                                delete_after=2)

    @ui.button(label="Leave", style=ButtonStyle.gray, custom_id='leave')
    async def leave_button(self, interaction: discord.Interaction, button: ui.Button):
        jm = JoinableMessage(interaction.message, self.bot)
        if not await jm.is_joined(interaction.user):
            await interaction.response.send_message(f':x: You are not in this channel', ephemeral=True, delete_after=2)
            return
        await jm.remove_user(interaction.user)
        await interaction.response.send_message(f'You left channel <#{jm.get_channel_id()}>', ephemeral=True, delete_after=2)
