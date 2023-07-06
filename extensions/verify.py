import re

import discord
from discord.ext import commands
from discord.ext.commands import Context
from discordpy import bot

import config


@commands.hybrid_command(help='Mods only')
@commands.has_role(config.role['global_mod'])
async def verify(ctx: Context, user: str):
    user = re.findall(r"\d+", user) or None
    if user is None:
        await ctx.send(':x: Invalid user mention or id', ephemeral=True)
    user = int(user[0])
    user = ctx.guild.get_member(user)
    role = ctx.guild.get_role(config.role['user'])
    if role in user.roles:
        await ctx.send(f':x: Member {user.mention} is already verified', ephemeral=True)
        return
    await user.add_roles(role, reason=f'User verified by {ctx.author}')
    channel = ctx.guild.get_channel_or_thread(config.channel['general'])
    await ctx.send(f'Verified member {user.mention}', ephemeral=True)
    emoji = [emote for emote in ctx.guild.emojis if emote.name == 'pikawave'][0]
    print(f'User {user} verified by {ctx.author}')
    await channel.send(
        f'Welkom {user.mention}! <a:{emoji.name}:{emoji.id}>\n'
        f'Kijk in de <#513719588165386241> voor meer informatie.'
    )


@bot.tree.context_menu(name='Verify User')
async def verify_user(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.get_role(config.role['global_mod']) is None:
        print(f'User {interaction.user} tried to verify {user}, no permissions')
        await interaction.response.send_message(f':no_entry: This command is for moderators only.', ephemeral=True, delete_after=3)
        return
    role = interaction.guild.get_role(config.role['user'])
    if role in user.roles:
        await interaction.response.send_message(f':x: Member {user.mention} is already verified', ephemeral=True, delete_after=10)
        return
    await user.add_roles(role, reason=f'User verified by {interaction.user}')
    channel = interaction.guild.get_channel_or_thread(config.channel['general'])
    await interaction.response.send_message(f':white_check_mark: Verified member {user.mention}', ephemeral=True, delete_after=10)
    emoji = [emote for emote in interaction.guild.emojis if emote.name == 'pikawave'][0]
    print(f'User {user} verified by {interaction.user}')
    await channel.send(
        f'Welkom {user.mention}! <a:{emoji.name}:{emoji.id}>\n'
        f'Kijk in de <#513719588165386241> voor meer informatie.'
    )



async def setup(bot):
    bot.add_command(verify)
    bot.tree.add_command(verify_user)
