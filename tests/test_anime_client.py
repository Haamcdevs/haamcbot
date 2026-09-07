from anilist.anime import AnimeClient


def test_anime_def_returns_none_when_response_data_is_none():
    assert AnimeClient().anime_def({'data': None}) is None


def test_anime_def_returns_none_when_media_is_none():
    assert AnimeClient().anime_def({'data': {'Media': None}}) is None


def test_anime_def_parses_valid_media():
    anime = AnimeClient().anime_def({
        'data': {
            'Media': {
                'id': 1,
                'genres': ['Comedy'],
                'description': '<b>Hello</b><br>world',
                'episodes': 12,
                'startDate': {'year': 2024, 'month': 4, 'day': 1},
                'season': 'SPRING',
                'seasonYear': 2024,
                'coverImage': {'extraLarge': 'image.png'},
                'trailer': {'id': 'abc123'},
                'title': {'romaji': 'Romaji', 'english': 'English'},
                'nextAiringEpisode': {'episode': 2},
                'airingSchedule': {
                    'edges': [
                        {'node': {'airingAt': 123, 'episode': 1}},
                        {'node': {'airingAt': 456, 'episode': 2}},
                    ]
                },
                'characters': {
                    'edges': [
                        {
                            'node': {
                                'id': 7,
                                'description': 'Lead',
                                'name': {'userPreferred': 'Hero'},
                                'image': {'large': 'hero.png'},
                            }
                        }
                    ]
                },
            }
        }
    })

    assert anime == {
        'id': 1,
        'name': 'English',
        'episodes': 12,
        'trailer': 'https://www.youtube.com/watch?v=abc123',
        'genres': ['Comedy'],
        'season_year': 2024,
        'season': 'SPRING',
        'starts_at': '1-4-2024',
        'image': 'image.png',
        'description': '**Hello**\nworld',
        'airdates': [
            {'time': 123, 'episode': 1},
            {'time': 456, 'episode': 2},
        ],
        'characters': [
            {
                'id': 7,
                'name': 'Hero',
                'image': 'hero.png',
                'description': 'Lead',
            }
        ]
    }
