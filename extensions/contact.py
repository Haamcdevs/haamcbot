import discord
from discord import Interaction, TextStyle
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import TextInput, Modal
from discordpy import bot

import config


class ContactForm(Modal):
    def __init__(self):
        super().__init__(title='Contacteer het mod team')
        self.description = TextInput(
            label='Contacteer het mod team',
            placeholder='Zet hier je bericht',
            style=TextStyle.long,
            max_length=1900
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: Interaction):
        print(f'{interaction.user} submitted mod contact form')
        channel = interaction.guild.get_channel(config.channel['admin_chat'])
        message = f'<@&{config.role["global_mod"]}> **-Mod Contact-**\n' \
                  f'**Reporter:** {interaction.user.mention}\n' \
                  f'**Comment:** {self.description.value}\n'

        await channel.send(message)
        if interaction.is_expired():
            print('timed out')
            return
        await interaction.response.send_message(
            'We hebben je bericht goed ontvangen, en nemen indien nodig met je contact op.',
            ephemeral=True
        )


@commands.hybrid_command(help='Send a message to our mod team')
@commands.has_role(config.role['user'])
async def contact_mods(ctx: Context):
    modal = ContactForm()
    await ctx.interaction.response.send_modal(modal)


@bot.tree.context_menu(name='Contact moderators')
async def contact(interaction: discord.Interaction, message: discord.Message):
    if interaction.user.get_role(config.role['user']) is None:
        await interaction.response.send_message(
            f':no_entry: This command is for verified users only.',
            ephemeral=True,
            delete_after=3
        )
        return
    modal = ContactForm()
    await interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(contact_mods)
    bot.tree.add_command(contact)
