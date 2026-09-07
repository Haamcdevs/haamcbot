import asyncio

import mysql.connector
import pytest

import cogs.anime_notification as anime_notification
from anilist.models import Anime
from cogs.anime_notification import Notifications


class FakePost:
    def __init__(self):
        self.reactions = []

    async def add_reaction(self, reaction):
        self.reactions.append(reaction)


class FakeChannel:
    def __init__(self, error=None):
        self.error = error
        self.messages = []
        self.posts = []

    async def send(self, content):
        if self.error is not None:
            raise self.error
        self.messages.append(content)
        self.posts.append(FakePost())
        return self.posts[-1]


class FakeGuild:
    def __init__(self, channels):
        self.channels = channels

    def get_channel_or_thread(self, channel_id):
        return self.channels.get(channel_id)


class FakeBot:
    def __init__(self, guilds):
        self.guilds = guilds
        self.presence = []

    def is_ready(self):
        return True

    def get_guild(self, guild_id):
        return self.guilds.get(guild_id)

    async def change_presence(self, status=None, activity=None):
        self.presence.append(activity)


class FakeAiring:
    def __init__(self, notifications, load_error=None, remove_errors=()):
        self.notifications = list(notifications)
        self.load_error = load_error
        self.remove_errors = set(remove_errors)
        self.removed = []
        self.cleared = []
        self.updated = []
        self.reconnects = 0

    def load_current_notifications(self):
        if self.load_error is not None:
            raise self.load_error
        return [row for row in self.notifications if row['id'] not in self.removed]

    def remove_notification(self, notification_id):
        self.removed.append(notification_id)
        if notification_id in self.remove_errors:
            raise mysql.connector.errors.DatabaseError('connection lost')

    def clear_channel(self, channel_id):
        self.cleared.append(channel_id)

    def add_notifications_to_channel(self, channel_id, guild_id, anime):
        self.updated.append((channel_id, anime.id))

    def reconnect(self):
        self.reconnects += 1


def notification(notification_id, anime_id=None, channel_id=None, guild_id=1, name=b'Anime'):
    return {
        'id': notification_id,
        'anime_id': anime_id if anime_id is not None else notification_id,
        'channel_id': channel_id if channel_id is not None else 100 + notification_id,
        'guild_id': guild_id,
        'episode': notification_id,
        'anime_name': name,
        'airing': 1700000000,
    }


@pytest.fixture
def anilist(monkeypatch):
    """Answers by_id from a dict of anime id -> Anime, or raises when the value is an exception."""
    responses = {}

    class FakeAnimeClient:
        async def by_id(self, anime_id):
            answer = responses.get(anime_id, Anime(id=anime_id))
            if isinstance(answer, Exception):
                raise answer
            return answer

    monkeypatch.setattr(anime_notification, 'AnimeClient', FakeAnimeClient)
    return responses


def run_loop(bot, airing):
    cog = Notifications(bot)
    cog.airing = airing
    asyncio.run(cog.notify_anime_channel())
    return cog


def test_sends_a_notification_for_every_channel(anilist):
    channels = {101: FakeChannel(), 102: FakeChannel()}
    bot = FakeBot({1: FakeGuild(channels)})
    airing = FakeAiring([notification(1), notification(2)])

    run_loop(bot, airing)

    assert len(channels[101].messages) == 1
    assert len(channels[102].messages) == 1
    assert airing.removed == [1, 2]
    assert bot.presence[-1].state == 'Anime ep. 2'


def test_a_failing_send_does_not_block_the_other_notifications(anilist):
    channels = {101: FakeChannel(error=RuntimeError('missing permissions')), 102: FakeChannel()}
    bot = FakeBot({1: FakeGuild(channels)})
    airing = FakeAiring([notification(1), notification(2)])

    run_loop(bot, airing)

    assert channels[102].messages, 'the second anime should still be announced'
    assert airing.removed == [1, 2], 'a notification that cannot be sent is dropped, not retried forever'
    assert bot.presence[-1].state == 'Anime ep. 2'


def test_a_missing_guild_does_not_block_the_other_notifications(anilist):
    channels = {102: FakeChannel()}
    bot = FakeBot({1: FakeGuild(channels)})
    airing = FakeAiring([notification(1, guild_id=999), notification(2)])

    run_loop(bot, airing)

    assert channels[102].messages
    assert airing.removed == [1, 2]


def test_a_failing_removal_does_not_block_the_other_notifications(anilist):
    channels = {101: FakeChannel(), 102: FakeChannel()}
    bot = FakeBot({1: FakeGuild(channels)})
    airing = FakeAiring([notification(1), notification(2)], remove_errors=[1])

    run_loop(bot, airing)

    assert channels[102].messages


def test_a_failing_anime_lookup_does_not_block_the_other_schedules(anilist):
    anilist[1] = RuntimeError('anilist is down')
    anilist[3] = None  # AniList answered, but without a Media
    channels = {101: FakeChannel(), 102: FakeChannel(), 103: FakeChannel()}
    bot = FakeBot({1: FakeGuild(channels)})
    airing = FakeAiring([notification(1), notification(2), notification(3)])

    run_loop(bot, airing)

    assert airing.updated == [(102, 2)], 'only the anime that resolved should be rescheduled'
    assert channels[102].messages


def test_clears_channels_that_no_longer_exist(anilist):
    bot = FakeBot({1: FakeGuild({})})
    airing = FakeAiring([notification(1)])

    run_loop(bot, airing)

    assert airing.cleared == [101]
    assert airing.updated == []


def test_a_database_failure_skips_the_run(anilist):
    bot = FakeBot({1: FakeGuild({101: FakeChannel()})})
    airing = FakeAiring([notification(1)], load_error=mysql.connector.errors.DatabaseError('gone'))

    run_loop(bot, airing)

    assert airing.reconnects > 0
    assert airing.removed == []


def test_adds_the_rating_reactions(anilist):
    channel = FakeChannel()
    bot = FakeBot({1: FakeGuild({101: channel})})
    airing = FakeAiring([notification(1)])

    run_loop(bot, airing)

    assert channel.messages[0].startswith('Aflevering **1** van **Anime**')
    assert channel.posts[0].reactions == ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
