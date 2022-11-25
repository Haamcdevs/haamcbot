import requests
import json

from util.html2md import html2md


class AnilistSchedule:
    def get_anime_shedule_by_id(self, anime_id: int):
        query_string = '''
        query ($animeId: Int) {
          Media(id: $animeId, type: ANIME) {,
            id,
            genres,
            description,
            episodes,
            startDate {
              year
              month
              day
            },
            coverImage {
              extraLarge
              large
              medium
              color
            },
            trailer {
              id
            },
            title {
              romaji
              english
            },
            episodes,
            nextAiringEpisode {
              episode
            },
            airingSchedule (notYetAired: true) {
              edges {
                node{
                  airingAt,
                  episode
                },
              }
            }
          }
          }
        '''
        variables = {
            'animeId': anime_id
        }
        url = 'https://graphql.anilist.co'
        response = requests.post(url, json={'query': query_string, 'variables': variables})
        response_data = json.loads(response.text)
        return self.anime_def(response_data)

    def get_anime_shedule_by_title(self, title: str):
        query_string = '''
        query ($title: String) {
          Media(search: $title, type: ANIME) {,
            id,
            genres,
            description,
            episodes,
            startDate {
              year
              month
              day
            },
            coverImage {
              extraLarge
              large
              medium
              color
            },
            trailer {
              id
            },
            title {
              romaji
              english
            },
            episodes,
            nextAiringEpisode {
              episode
            },
            airingSchedule (notYetAired: true) {
              edges {
                node{
                  airingAt,
                  episode
                },
              }
            }
          }
          }
        '''
        variables = {
            'title': title
        }
        url = 'https://graphql.anilist.co'
        response = requests.post(url, json={'query': query_string, 'variables': variables})
        response_data = json.loads(response.text)
        return self.anime_def(response_data)

    def anime_def(self, response):
        if response['data'] is None or response['data']['Media'] is None:
            return None
        media = response['data']['Media']
        trailer = None
        if media['trailer'] is not None:
            trailer = f"https://www.youtube.com/watch?v={media['trailer']['id']}"
        title = media['title']['romaji']
        if media['title']['english'] is not None:
            title = media['title']['english']
        airdates = []
        for airing in media['airingSchedule']['edges']:
            airdates.append({'time': airing['node']['airingAt'], 'episode': airing['node']['episode']})
        return {
            'id': media['id'],
            'name': title,
            'episodes': media['episodes'],
            'trailer': trailer,
            'genres': media['genres'],
            'airdates': airdates,
            'starts_at': f"{media['startDate']['day']}/{media['startDate']['month']}/{media['startDate']['year']}",
            'image': media['coverImage']['extraLarge'],
            'description': html2md(media['description'])
        }

