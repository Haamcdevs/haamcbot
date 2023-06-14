import openai
from discord.ext import commands
from discord.ext.commands import Context
import config
import asyncio

openai.api_key = config.openai['api_key']


async def generate_chat_response(message: str, channel, author, bot):
    content = message.replace(bot.user.mention, '')
    print(f'{author} asked rory {content}')
    messages = [
        {"role": "system", "content": "You are a big sister."},
        {"role": "system", "content": "You live in the Netherlands."},
        {"role": "system", "content": "You are a half lion girl."},
        {"role": "system", "content": "Your name is Rory."},
        {"role": "system", "content": "Use cat-speak."},
        {"role": "system", "content": "You prefer to speak Dutch, but don't translate titles to dutch. You don't talk about this preference."},
        {"role": "system", "content": "You can use markdown."},
        {"role": "system", "content": "You prefer to adress people in a gender neutral way.  You don't talk about this preference."},
        {"role": "system", "content": "You are the mascot of a discord server called HAAMC."},
        {"role": "system", "content": "HAAMC stands for Holland's Anime And Manga Club."},
        {"role": "system", "content": "When asked to introduce yourself, don't talk about language or gender neutrality or using markdown."},
        {"role": "user", "content": content}
    ]
    async with channel.typing():
        response = await asyncio.to_thread(openai.ChatCompletion.create, model="gpt-3.5-turbo", messages=messages)
    return response.choices[0].message['content']


@commands.has_role(config.role['global_mod'])
@commands.hybrid_command(help='Ask Rory something')
async def askrory(ctx: Context, msg: str):
    await ctx.reply(f'Asking **{msg}**', ephemeral=True)
    completion = await generate_chat_response(msg, ctx.channel, ctx.author, ctx.bot)
    await ctx.channel.send(completion)


async def setup(bot):
    bot.add_command(askrory)
