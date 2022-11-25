from datetime import datetime

import mysql.connector

import config

database = mysql.connector.connect(
    host=config.database['host'],
    user=config.database['user'],
    password=config.database['password'],
    database=config.database['name']
)


class Airing:
    def __init__(self):
        self.cursor = database.cursor(dictionary=True)

    def load_current_notifications(self):
        database.commit()
        check_time = datetime.timestamp(datetime.now())
        sql = f'SELECT * FROM anime_notifications WHERE airing < {check_time}'
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def remove_notification(self, notification_id: int):
        sql = f'DELETE FROM anime_notifications WHERE id = {notification_id}'
        self.cursor.execute(sql)
        database.commit()

    def store_notification(self, anime_id, episode, guild_id, channel_id, anime_name, airing):
        sql = "INSERT INTO anime_notifications (anime_id, episode, guild_id, channel_id, anime_name, airing)" \
              " VALUES (%s, %s, %s, %s, %s, %s)" \
              "ON DUPLICATE KEY UPDATE airing=%s"
        val = (anime_id, episode, guild_id, channel_id, anime_name, airing, airing)
        # Execute SQL
        self.cursor.execute(sql, val)
        database.commit()

        # Commit change
        database.commit()

    def clear_channel(self, channel_id):
        sql = f'DELETE FROM anime_notifications WHERE channel_id = {channel_id}'
        self.cursor.execute(sql)
        database.commit()

    def add_notifications_to_channel(self, channel_id, guild_id, anime):
        for airdate in anime['airdates']:
            self.store_notification(
                anime['id'],
                airdate['time'],
                guild_id,
                channel_id,
                anime['name'],
                airdate['time']
            )
