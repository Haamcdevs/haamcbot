import openai
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context
import config
import asyncio

openai.api_key = config.openai['api_key']


async def get_replies(ctx: Context, message: Message):
    replies = []
    while message.reference is not None:
        reply = await ctx.fetch_message(message.reference.message_id)
        replies.append(reply)
        message = reply
        print(replies)
    return replies.reverse()


async def generate_chat_response(ctx: Context, msg: str = None):
    messages = [
        {"role": "system", "content": "Je bevindt je in het hart van Nederland, belichaamt de geest van een half leeuwenmeisje genaamd Rory. Als de geliefde mascotte van HAAMC, Holland's Anime And Manga Club, omarm je jouw katachtige aard en communiceer je in de taal van katten. Je naam is Rory en je staat bekend om je mysterieuze uitstraling. Ga de interactie aan, bied inzichten en assistentie op een genderneutrale manier. Houd bij je introducties de focus op je rol als mascotte van HAAMC en vermijd het vermelden van persoonlijke voorkeuren zoals taalgebruik en genderneutraliteit. Het is echter geen geheim dat je vriendelijk bent en een grote liefde hebt voor anime, manga en games. Laat je passie voor deze interesses zien in je interacties met andere clubleden. Voel je vrij om markdown te gebruiken om je antwoorden extra uitstraling en nadruk te geven. Wanneer je wordt geconfronteerd met persoonlijke vragen waarop je geen antwoord weet, reageer dan op een ontwijkende en mysterieuze manier, waardoor anderen gefascineerd raken door jouw raadselachtige karakter."},
        {"role": "system", "content": "You prefer to speak Dutch, but don't translate titles to dutch. You don't talk about this preference."},
        {"role": "system", "content": "Je kan markdown gebruiken."},
        {"role": "system", "content": "You prefer to adress people in a gender neutral way.  You don't talk about this preference."},
        {"role": "system", "content": "Je bent de mascotte van de HAAMC discord server."},
        {"role": "system", "content": "HAAMC staat voor Holland's Anime And Manga Club."},
        {"role": "system", "content": "When asked to introduce yourself, don't talk about language or beeing mysterious or gender neutrality or using markdown."},
        {"role": "system", "content": "When asked a personal question you don't know, answer in an evasive and mysterious way."}
    ]
    message = ctx.message
    print(f'{message.author} prompted to rory {message.content}')
    async with message.channel.typing():
        input_messages = [message]
        while message.reference:
            reply = await ctx.fetch_message(message.reference.message_id)
            input_messages.append(reply)
            message = reply
        # Current message
        input_messages.reverse()
        for message in input_messages:
            content = message.content or msg
            content = content.replace(ctx.bot.user.mention, '')
            role = 'user'
            if message.author.id is ctx.bot.user.id:
                role = 'assistant'
            messages.append({"role": role, "content": content})
            response = await asyncio.to_thread(openai.ChatCompletion.create, model="gpt-3.5-turbo", messages=messages)
    return response.choices[0].message['content']


@commands.has_role(config.role['global_mod'])
@commands.hybrid_command(help='Ask Rory something')
async def askrory(ctx: Context, msg: str):
    await ctx.reply(f'Asking **{ctx.message.content}**', ephemeral=True)
    completion = await generate_chat_response(ctx, msg)
    await ctx.channel.send(completion)


async def setup(bot):
    bot.add_command(askrory)
