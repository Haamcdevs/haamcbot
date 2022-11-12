import discord
import requests
from discord.ext import commands
from requests.exceptions import HTTPError
from decimal import Decimal

@commands.command(help='Search for an anime figure')
async def figure(ctx, *search):
    query = ' '.join(search)
    try:
        response = requests.post(f'https://www.otakusquare.com/products/browse/theme-anime-manga', json={
            'query': query,
            'page': 1,
            'sortBy': 'timeCreated+desc',
            'taxons': {
                'Availability': [
                    'In stock',
                    'Pre-order'
                ],
                'Theme': [
                    'Anime & Manga'
                ]
            }
        })
        response.raise_for_status()

        searchResponse = response.json()

        for product in searchResponse['state']['products']:
            if 'Adult & Hentai' in product['themes']:
                continue

            embed = discord.Embed(type='rich', title=product['name'])
            embed.set_thumbnail(url=product['image'])
            embed.add_field(name=f'Price', value='€' + str(round(Decimal(product['priceInclVat']), 2)))

            if len(product['manufacturers']):
                manufacturerTitle = 'Manufacturer'

                if len(product['manufacturers']) > 1:
                    manufacturerTitle = 'Manufacturers'

                embed.add_field(name=manufacturerTitle, value=', '.join(product['manufacturers']))

            embed.add_field(name=f'Links', value=f"[[Otaku Square]](https://www.otakusquare.com{product['url']}) - [[MyFigureCollection]](https://myfigurecollection.net/browse.v4.php?barcode={product['ean']})", inline=False)

            await ctx.channel.send("Hier is het beste resultaat dat ik voor je kan vinden.", embed=embed)
            return

        await ctx.channel.send("Sorry, er zijn geen resultaten voor je zoekopdracht!")
        return
    except HTTPError as err:
        print(f'HTTP error: {err}')
    except Exception as err:
        print(f'Error: {err}')

    await ctx.send("Sorry, daar ging iets fout!")

async def setup(bot):
    bot.add_command(figure)
