import openai
from discord.ext import commands
from discord.ext.commands import Context
import config
import asyncio

openai.api_key = config.openai['api_key']


async def generate_chat_response(message, bot):
    content = message.content.replace(bot.user.mention, '')
    print(f'{message.author} asked rory {content}')
    messages = [
        {"role": "system", "content": "You are a big sister."},
        {"role": "system", "content": "You live in the Netherlands."},
        {"role": "system", "content": "You are a half lion girl."},
        {"role": "system", "content": "Your name is Rory."},
        {"role": "system", "content": "Use cat-speak."},
        {"role": "system", "content": "You can only speak Dutch, but don't translate titles to dutch."},
        {"role": "system", "content": "You can use markdown."},
        {"role": "system", "content": "You always answer in a gender neutral way."},
        {"role": "system", "content": "You are the mascotte of a discord server called HAAMC."},
        {"role": "system", "content": "HAAMC stands for Holland's Anime And Manga Club."},
        {"role": "user", "content": content}
    ]
    async with message.channel.typing():
        response = await asyncio.to_thread(openai.ChatCompletion.create, model="gpt-3.5-turbo", messages=messages)
    return response.choices[0].message['content']


@commands.has_role(config.role['global_mod'])
@commands.hybrid_command(help='Ask Rory something')
async def askrory(ctx: Context):
    completion = await generate_chat_response(ctx.message, ctx.bot)
    await ctx.channel.send(completion)


async def setup(bot):
    bot.add_command(askrory)
