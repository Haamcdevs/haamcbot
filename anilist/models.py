from typing import Any, List, Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator, model_validator

from util.html2md import html2md


class Airdate(BaseModel):
    episode: Optional[int] = Field(default=None, validation_alias=AliasPath('node', 'episode'))
    time: Optional[int] = Field(default=None, validation_alias=AliasPath('node', 'airingAt'))


class Character(BaseModel):
    id: Optional[int] = Field(default=None, validation_alias=AliasPath('node', 'id'))
    name: Optional[str] = Field(default=None, validation_alias=AliasPath('node', 'name', 'userPreferred'))
    image: Optional[str] = Field(default=None, validation_alias=AliasPath('node', 'image', 'large'))
    description: Optional[str] = Field(default=None, validation_alias=AliasPath('node', 'description'))


class Anime(BaseModel):
    """An AniList Media, flattened to what the bot uses. Absent and null fields fall back to the defaults."""

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    episodes: Optional[int] = None
    season: Optional[str] = None
    season_year: Optional[int] = Field(default=None, validation_alias='seasonYear')
    genres: List[str] = Field(default_factory=list)
    description: str = ''
    romaji: Optional[str] = Field(default=None, validation_alias=AliasPath('title', 'romaji'))
    english: Optional[str] = Field(default=None, validation_alias=AliasPath('title', 'english'))
    trailer_id: Optional[str] = Field(default=None, validation_alias=AliasPath('trailer', 'id'))
    cover: Optional[str] = Field(default=None, validation_alias=AliasPath('coverImage', 'extraLarge'))
    cover_fallback: Optional[str] = Field(default=None, validation_alias=AliasPath('coverImage', 'large'))
    day: Optional[int] = Field(default=None, validation_alias=AliasPath('startDate', 'day'))
    month: Optional[int] = Field(default=None, validation_alias=AliasPath('startDate', 'month'))
    year: Optional[int] = Field(default=None, validation_alias=AliasPath('startDate', 'year'))
    airdates: List[Airdate] = Field(default_factory=list, validation_alias=AliasPath('airingSchedule', 'edges'))
    characters: List[Character] = Field(default_factory=list, validation_alias=AliasPath('characters', 'edges'))

    @field_validator('genres', 'airdates', 'characters', mode='before')
    @classmethod
    def null_as_empty(cls, value: Any) -> Any:
        # An alias path that resolves to null is a value, not a missing key, so it never hits the default.
        return [] if value is None else value

    @field_validator('description', mode='before')
    @classmethod
    def as_markdown(cls, value: Any) -> str:
        return html2md(value or '')

    @field_validator('airdates', mode='after')
    @classmethod
    def drop_unscheduled(cls, airdates: List[Airdate]) -> List[Airdate]:
        return [airdate for airdate in airdates if airdate.episode is not None and airdate.time is not None]

    @model_validator(mode='after')
    def count_episodes(self) -> 'Anime':
        if self.episodes is None:
            self.episodes = len(self.airdates) or None
        return self

    @property
    def name(self) -> Optional[str]:
        return self.english or self.romaji

    @property
    def image(self) -> Optional[str]:
        return self.cover or self.cover_fallback

    @property
    def trailer(self) -> Optional[str]:
        if self.trailer_id is None:
            return None
        return f'https://www.youtube.com/watch?v={self.trailer_id}'

    @property
    def starts_at(self) -> str:
        return f"{self.day or '?'}-{self.month or '?'}-{self.year or '?'}"


class AnimeResponse(BaseModel):
    anime: Optional[Anime] = Field(default=None, validation_alias=AliasPath('data', 'Media'))
