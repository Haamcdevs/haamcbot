from discord import Interaction, TextStyle
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import TextInput, Modal

import config


class ContactForm(Modal):
    def __init__(self, ctx: Context):
        super().__init__(title='Contacteer het mod team')
        self.ctx = ctx
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
        source_channel = interaction.guild.get_channel_or_thread(interaction.channel.id)
        link = ''
        async for msg in source_channel.history(limit=1, before=interaction.message):
            link = msg.jump_url
            break
        message = f'**-Mod Contact-**\n' \
                  f'**Context:** {link}\n' \
                  f'**From:** {interaction.user.mention}\n' \
                  f'```\n{self.description.value}\n```'

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
    modal = ContactForm(ctx)
    await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    bot.add_command(mods)
