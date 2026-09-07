from typing import Optional

import aiohttp
from pydantic import ValidationError

from anilist.models import Anime, AnimeResponse

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
          description,
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
    url = 'https://graphql.anilist.co'

    async def by_id(self, anime_id: int) -> Optional[Anime]:
        query_string = 'query ($animeId: Int) {Media(id: $animeId, type: ANIME) {' + animeStructure + '}}'
        return await self.fetch(query_string, {'animeId': anime_id})

    async def by_title(self, title: str) -> Optional[Anime]:
        query_string = 'query ($title: String) {Media(search: $title, type: ANIME) {' + animeStructure + '}}'
        return await self.fetch(query_string, {'title': title})

    async def fetch(self, query_string: str, variables: dict) -> Optional[Anime]:
        payload = {'query': query_string, 'variables': variables}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    response_data = await response.json(content_type=None)
            media = AnimeResponse.model_validate(response_data).data.media
        except (aiohttp.ClientError, ValueError, ValidationError) as error:
            print(f'anilist: request for {variables} failed: {error}')
            return None
        if media is None:
            return None
        return Anime.from_media(media)
