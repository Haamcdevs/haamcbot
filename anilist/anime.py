import aiohttp

from util.html2md import html2md

animeStructure = '''
    id
    genres
    description
    episodes
    startDate {
      year
      month
      day
    },
    season,
    seasonYear,
    coverImage {
      extraLarge
      large
      medium
      color
    }
    trailer {
      id
    }
    title {
      romaji
      english
    }
    episodes
    nextAiringEpisode {
      episode
    }
    airingSchedule (notYetAired: true) {
      edges {
        node {
          airingAt
          episode
        }
      }
    }
    characters (sort:FAVOURITES_DESC) {
      edges {
        node {
          id,
          name {
            userPreferred
          },
          image {
            large
          }
        },
      }
    }
'''


class AnimeClient:
    async def by_id(self, anime_id: int):
        query_string = 'query ($animeId: Int) {Media(id: $animeId, type: ANIME) {' + animeStructure + '}}'
        variables = {
            'animeId': anime_id
        }
        url = 'https://graphql.anilist.co'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={'query': query_string, 'variables': variables}) as response:
                response_data = await response.json()
        return self.anime_def(response_data)

    async def by_title(self, title: str):
        query_string = 'query ($title: String) {Media(search: $title, type: ANIME) {' + animeStructure + '}}'
        variables = {
            'title': title
        }
        url = 'https://graphql.anilist.co'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={'query': query_string, 'variables': variables}) as response:
                response_data = await response.json()
        return self.anime_def(response_data)

    def anime_def(self, response):
        if response['data'] is None or response['data']['Media'] is None:
            return None
        media = response['data']['Media']
        trailer = None
        if media['trailer'] is not None:
            trailer = 'https://www.youtube.com/watch?v=' + media['trailer']['id']
        title = media['title']['romaji']
        if media['title']['english'] is not None:
            title = media['title']['english']
        airdates = self.parse_airing(media)
        characters = self.parse_characters(media)
        return {
            'id': media['id'],
            'name': title,
            'episodes': media['episodes'],
            'trailer': trailer,
            'genres': media['genres'],
            'season_year': media['seasonYear'],
            'season': media['season'],
            'starts_at': f"{media['startDate']['day'] or '?'}-"
                         f"{media['startDate']['month'] or '?'}-"
                         f"{media['startDate']['year'] or '?'}",
            'image': media['coverImage']['extraLarge'],
            'description': html2md(media['description'] or ''),
            'airdates': airdates,
            'characters': characters
        }

    def parse_airing(self, media):
        airdates = []
        for airing in media['airingSchedule']['edges']:
            airdates.append({'time': airing['node']['airingAt'], 'episode': airing['node']['episode']})
        return airdates

    def parse_characters(self, media):
        characters = []
        for character in media['characters']['edges']:
            characters.append({
                'id': character['node']['id'],
                'name': character['node']['name']['userPreferred'],
                'image': character['node']['image']['large']
            })
        return characters
