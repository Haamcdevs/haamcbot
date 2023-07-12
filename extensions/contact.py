import discord
from discord import Interaction, TextStyle
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import TextInput, Modal
from discordpy import bot

import config


class ContactForm(Modal):
    def __init__(self, message: discord.Message):
        super().__init__(title='Contacteer het mod team')
        self.message: discord.Message = message
        self.description = TextInput(
            label='Wat is er aan de hand',
            placeholder='Leg hier uit wat er aan de hand is',
            style=TextStyle.long,
            max_length=1900
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: Interaction):
        print(f'{interaction.user} submitted mod contact form')
        channel = interaction.guild.get_channel(config.channel['admin_chat'])
        message = f'<@&{config.role["global_mod"]}> **-Mod Contact-**\n' \
                  f'**Message link:** {self.message.jump_url}\n' \
                  f'**Message author:** {self.message.author.mention}\n' \
                  f'**Message content:** {self.message.content}\n' \
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


@commands.hybrid_command(help='MOOOOOODS... Send a message to our mod team')
@commands.has_role(config.role['user'])
async def mods(ctx: Context):
    async for msg in ctx.channel.history(limit=1, before=ctx.message):
        reported_message = msg
        break
    modal = ContactForm(reported_message)
    await ctx.interaction.response.send_modal(modal)


@bot.tree.context_menu(name='Report message')
async def report(interaction: discord.Interaction, message: discord.Message):
    if interaction.user.get_role(config.role['user']) is None:
        await interaction.response.send_message(
            f':no_entry: This command is for verified users only.',
            ephemeral=True,
            delete_after=3
        )
        return
    modal = ContactForm(message)
    await interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(mods)
    bot.tree.add_command(report)
