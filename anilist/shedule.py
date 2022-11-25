import requests
import json


class AnilistSchedule:
    @staticmethod
    def get_anime_shedule_by_id(anime_id: int):
        query_string = '''
        query ($animeId: Int) {
          Media(id: $animeId, type: ANIME) {
            id,
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
        return response_data

    @staticmethod
    def get_anime_shedule_by_title(title: str):
        query_string = '''
        query ($title: String) {
          Media(search: $title, type: ANIME) {,
            id,
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
        return response_data

#print(AnilistShedule.get_anime_shedule_by_title('One piece'))
