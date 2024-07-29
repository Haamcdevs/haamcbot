import asyncio

from discord import Member, ScheduledEvent
from discord.ext import commands

import config
from discord.ext.commands import Cog, Context


class EventCreate(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_scheduled_event_create(self, event: ScheduledEvent):
        channel = event.guild.get_channel_or_thread(config.channel['events'])
        message = await channel.send(f'https://discord.com/events/{event.guild.id}/{event.id}')
        thread = await message.create_thread(name=f'{event.name}')
        await event.edit(
            location=f'<#{thread.id}>'
        )
        print(f'Event created: {event.id} / {event.name}')

    @Cog.listener()
    async def on_scheduled_event_update(self, before: ScheduledEvent, after: ScheduledEvent):
        try:
            channel_id = int(before.location[2:-1])
        except ValueError:
            print(f'Invalid channel id: "{before.location}"')
            return
        channel = before.guild.get_thread(channel_id)
        if channel is None:
            print(f'Channel not found: "{channel_id}"')
            return
        await channel.edit(name=after.name)
        print(f'Event updated: {after.id} / {after.name}')


    @Cog.listener()
    async def on_scheduled_event_delete(self, event: ScheduledEvent):
        try:
            channel_id = int(event.location[2:-1])
        except ValueError:
            print(f'Invalid channel id: "{event.location}"')
            return
        thread = event.guild.get_thread(channel_id)
        if thread is None:
            print(f'Channel not found: "{channel_id}"')
            return
        await thread.starter_message.delete()
        print(f'Event deleted: {event.id} / {event.name}')


async def setup(bot):
    await bot.add_cog(EventCreate(bot))
