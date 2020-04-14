import requests
import xml.etree.ElementTree as ET
from discord.ext import commands


@commands.command()
async def weather(ctx, msg):
    if msg:
        city = " ".join(msg)
        currentweather = 'http://api.wunderground.com/auto/wui/geo/WXCurrentObXML/index.xml?query={}'.format(city)
        data = requests.get(currentweather)
        root = ET.fromstring(data.text)
        if not root[6].text:
            await ctx.send("Unknown place")
        else:
            txt = 'Current weather in {}:\n'.format(city)
            txt += 'Temperature: {}°C\n'.format(root[16].text)
            txt += 'Humidity: {}\n'.format(root[17].text)
            txt += 'Conditions: {}\n'.format(root[13].text)
            txt += 'Wind: {} @ {}km/h'.format(root[19].text, round(int(root[21].text) * 1.609344))
            await ctx.send(txt)
    else:
        await ctx.send('Please give a location.')


def setup(bot):
    bot.add_command(weather)
