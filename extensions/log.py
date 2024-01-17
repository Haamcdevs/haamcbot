import discord
from discord import Interaction, TextStyle
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import TextInput, Modal
from discordpy import bot

import config


class LogModal(Modal):
    def __init__(self):
        super().__init__(title='Log a moderator action')
        self.userid = TextInput(
            label='Userid',
            placeholder='3473924793478',
            max_length=1900
        )
        self.add_item(self.userid)
        self.description = TextInput(
            label='Wat is er aan de hand',
            placeholder='Leg hier uit wat er aan de hand is',
            style=TextStyle.long,
            max_length=1900
        )
        self.add_item(self.description)
        self.action = TextInput(
            label='Welke actie is er ondernomen',
            placeholder='DM, deleted message, etv',
            max_length=1900
        )
        self.add_item(self.action)
        self.agreement = TextInput(
            label='Welke afspraken zijn gemaakt',
            placeholder='Voorwaarden in DM afgesproken etc',
            style=TextStyle.long,
            max_length=1900
        )
        self.add_item(self.agreement)

    async def on_submit(self, interaction: Interaction):
        print(f'{interaction.user} submitted mod log')
        channel = interaction.guild.get_channel(config.channel['report'])
        message = f'**-Mod Log Entry-**\n' \
                  f'**Reporter:** {interaction.user.mention}\n' \
                  f'**User:** <@{self.userid.value}>\n' \
                  f'**Description:** {self.description.value}\n' \
                  f'**Action:** {self.action.value}\n' \
                  f'**Agreement:** {self.agreement.value}\n'

        await channel.send(message)
        if interaction.is_expired():
            print('timed out')
            return
        await interaction.response.send_message(
            'Mod actie is logged.',
            ephemeral=True
        )

@commands.hybrid_command(help='Log an officer action')
@commands.has_role(config.role['officer'])
async def log(ctx: Context):
    modal = LogModal()
    await ctx.interaction.response.send_modal(modal)

async def setup(bot):
    bot.add_command(log)

