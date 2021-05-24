import discord
from discord.ext import commands
import requests
import json
import datetime


@commands.command(help='Display Anilist user information')
async def anilist(ctx, username):
    query = '''
    query ($name: String) {
      User(name: $name) {
        id
        name
        statistics {
          anime {
            meanScore
            episodesWatched
            minutesWatched
            statuses {
              count
              status
            }
          }
        }
        favourites {
          anime(page: 1, perPage: 3) {
            nodes {
              title {
                english
              }
              siteUrl
            }
          }
        }
      }
    }
    '''

    # Define our query variables and values that will be used in the query request
    variables = {
        'name': username
    }

    url = 'https://graphql.anilist.co'

    # Make the HTTP Api request
    response = requests.post(url, json={'query': query, 'variables': variables})
    response_data = json.loads(response.text)

    if response_data['data']['User'] is None:
        print("Invalid username")
        return

    embed = discord.Embed(type='rich', title=f'{username}\'s Anilist profile',
                          url=f'https://anilist.co/user/{username}')

    user_favorites = response_data['data']['User']['favourites']['anime']['nodes']
    embed.description = '**Top 3 favorite anime:**\n'
    for favorite in user_favorites:
        embed.description += f"[{favorite['title']['english']}]({favorite['siteUrl']})\n"

    user_statistics = response_data['data']['User']['statistics']['anime']
    status_counts = {"CURRENT":     (0, ':green_heart: Watching'),
                     "COMPLETED":   (0, ':blue_heart: Completed'),
                     "PAUSED":      (0, ':yellow_heart: On Hold'),
                     "DROPPED":     (0, ':broken_heart: Dropped'),
                     "PLANNING":    (0, ':white_circle: Plan to Watch')}
    for status_data in user_statistics['statuses']:
        status_counts[status_data['status']] = (status_data['count'], status_counts[status_data['status']][1])

    for status in status_counts.values():
        embed.add_field(name=status[1], value=status[0])

    embed.add_field(name=':chart_with_upwards_trend: Episodes Watched', value=user_statistics['episodesWatched'])
    embed.add_field(name=':clock1: Days', value=round(user_statistics['minutesWatched']/60/24, 1))
    embed.add_field(name=':bar_chart: Mean Score', value=user_statistics['meanScore'])

    query_activity = '''
    query ($userid: Int) {
      Activity(userId: $userid, sort: ID_DESC) {
        ... on ListActivity {
          createdAt
        }
        ... on TextActivity {
          createdAt
        }
        ... on MessageActivity {
          createdAt
        }
      }
    }
    '''

    variables_activity = {
        'userid': response_data['data']['User']['id']
    }

    response_activity = requests.post(url, json={'query': query_activity, 'variables': variables_activity})
    response_data_activity = json.loads(response_activity.text)
    activity_time = response_data_activity['data']['Activity']['createdAt']
    time_converted = datetime.datetime.fromtimestamp(activity_time)

    embed.add_field(name=':busts_in_silhouette: Last Activity', value=time_converted)

    await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_command(anilist)
