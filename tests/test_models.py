from anilist.models import AnimeResponse

FULL_MEDIA = {
    'id': 1,
    'genres': ['Action'],
    'description': '<b>bold</b><br>line',
    'episodes': 12,
    'startDate': {'year': 2024, 'month': 10, 'day': 3},
    'season': 'FALL',
    'seasonYear': 2024,
    'coverImage': {'extraLarge': 'extra.jpg', 'large': 'large.jpg', 'medium': None, 'color': None},
    'trailer': {'id': 'abc123'},
    'title': {'romaji': 'Romaji', 'english': 'English'},
    'airingSchedule': {'edges': [{'node': {'airingAt': 100, 'episode': 1}}]},
    'characters': {'edges': [{'node': {
        'id': 5, 'description': 'desc', 'name': {'userPreferred': 'Bob'}, 'image': {'large': 'bob.jpg'}
    }}]},
}


def parse(media):
    return AnimeResponse.model_validate({'data': {'Media': media}}).anime


def test_parses_a_full_response():
    anime = parse(FULL_MEDIA)
    assert anime.id == 1
    assert anime.name == 'English'
    assert anime.episodes == 12
    assert anime.genres == ['Action']
    assert anime.season == 'FALL'
    assert anime.season_year == 2024
    assert anime.starts_at == '3-10-2024'
    assert anime.image == 'extra.jpg'
    assert anime.trailer == 'https://www.youtube.com/watch?v=abc123'
    assert anime.description == '**bold**\nline'
    assert [(airdate.episode, airdate.time) for airdate in anime.airdates] == [(1, 100)]
    assert [(c.id, c.name, c.image, c.description) for c in anime.characters] == [(5, 'Bob', 'bob.jpg', 'desc')]


def test_null_data_yields_no_anime():
    # AniList answers with a null data block on errors, rate limits and downtime.
    assert AnimeResponse.model_validate({'data': None, 'errors': [{'message': 'Too Many Requests'}]}).anime is None


def test_missing_data_yields_no_anime():
    assert AnimeResponse.model_validate({'errors': [{'message': 'boom'}]}).anime is None
    assert AnimeResponse.model_validate({}).anime is None


def test_unknown_anime_yields_no_anime():
    assert parse(None) is None


def test_null_nested_objects_fall_back_to_defaults():
    anime = parse({
        'id': 7, 'title': None, 'coverImage': None, 'startDate': None, 'trailer': None,
        'airingSchedule': None, 'characters': None, 'genres': None, 'description': None,
        'episodes': None, 'season': None, 'seasonYear': None,
    })
    assert anime.id == 7
    assert anime.name is None
    assert anime.image is None
    assert anime.trailer is None
    assert anime.starts_at == '?-?-?'
    assert anime.description == ''
    assert anime.genres == []
    assert anime.airdates == []
    assert anime.characters == []
    assert anime.episodes is None


def test_null_edges_fall_back_to_empty_lists():
    anime = parse({'id': 8, 'airingSchedule': {'edges': None}, 'characters': {'edges': None}})
    assert anime.airdates == []
    assert anime.characters == []


def test_falls_back_to_the_romaji_title_and_the_large_cover():
    anime = parse({'title': {'romaji': 'Romaji', 'english': None},
                   'coverImage': {'extraLarge': None, 'large': 'large.jpg'}})
    assert anime.name == 'Romaji'
    assert anime.image == 'large.jpg'


def test_counts_episodes_from_the_schedule_when_anilist_has_no_count():
    anime = parse(dict(FULL_MEDIA, episodes=None, airingSchedule={'edges': [
        {'node': {'airingAt': 100, 'episode': 1}},
        {'node': {'airingAt': 200, 'episode': 2}},
    ]}))
    assert anime.episodes == 2


def test_drops_episodes_without_a_schedule():
    anime = parse(dict(FULL_MEDIA, airingSchedule={'edges': [
        {'node': {'airingAt': 100, 'episode': 1}},
        {'node': {'airingAt': None, 'episode': 2}},
        {'node': None},
    ]}))
    assert [airdate.episode for airdate in anime.airdates] == [1]
