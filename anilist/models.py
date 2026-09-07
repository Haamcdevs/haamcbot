from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from util.html2md import html2md


class AnilistModel(BaseModel):
    """Base for the raw AniList shapes: unknown fields are ignored and nulls fall back to defaults."""

    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    @model_validator(mode='before')
    @classmethod
    def null_as_default(cls, data: Any) -> Any:
        # AniList returns null both for absent objects and for fields it failed to resolve.
        if data is None:
            return {}
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value is not None}
        return data


class Title(AnilistModel):
    romaji: Optional[str] = None
    english: Optional[str] = None

    @property
    def preferred(self) -> Optional[str]:
        return self.english or self.romaji


class CoverImage(AnilistModel):
    extra_large: Optional[str] = Field(default=None, alias='extraLarge')
    large: Optional[str] = None
    medium: Optional[str] = None
    color: Optional[str] = None

    @property
    def preferred(self) -> Optional[str]:
        return self.extra_large or self.large or self.medium


class Trailer(AnilistModel):
    id: Optional[str] = None

    @property
    def url(self) -> Optional[str]:
        if self.id is None:
            return None
        return f'https://www.youtube.com/watch?v={self.id}'


class StartDate(AnilistModel):
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.day or '?'}-{self.month or '?'}-{self.year or '?'}"


class AiringNode(AnilistModel):
    airing_at: Optional[int] = Field(default=None, alias='airingAt')
    episode: Optional[int] = None


class AiringEdge(AnilistModel):
    node: AiringNode = Field(default_factory=AiringNode)


class AiringSchedule(AnilistModel):
    edges: List[AiringEdge] = Field(default_factory=list)


class CharacterName(AnilistModel):
    user_preferred: Optional[str] = Field(default=None, alias='userPreferred')


class CharacterImage(AnilistModel):
    large: Optional[str] = None


class CharacterNode(AnilistModel):
    id: Optional[int] = None
    description: Optional[str] = None
    name: CharacterName = Field(default_factory=CharacterName)
    image: CharacterImage = Field(default_factory=CharacterImage)


class CharacterEdge(AnilistModel):
    node: CharacterNode = Field(default_factory=CharacterNode)


class CharacterConnection(AnilistModel):
    edges: List[CharacterEdge] = Field(default_factory=list)


class Media(AnilistModel):
    id: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    episodes: Optional[int] = None
    season: Optional[str] = None
    season_year: Optional[int] = Field(default=None, alias='seasonYear')
    start_date: StartDate = Field(default_factory=StartDate, alias='startDate')
    cover_image: CoverImage = Field(default_factory=CoverImage, alias='coverImage')
    trailer: Trailer = Field(default_factory=Trailer)
    title: Title = Field(default_factory=Title)
    airing_schedule: AiringSchedule = Field(default_factory=AiringSchedule, alias='airingSchedule')
    characters: CharacterConnection = Field(default_factory=CharacterConnection)


class ResponseData(AnilistModel):
    media: Optional[Media] = Field(default=None, alias='Media')


class AnimeResponse(AnilistModel):
    data: ResponseData = Field(default_factory=ResponseData)


class Airdate(BaseModel):
    episode: int
    time: int


class Character(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None


class Anime(BaseModel):
    """The anime as the bot uses it, flattened out of the AniList response."""

    id: Optional[int] = None
    name: Optional[str] = None
    episodes: Optional[int] = None
    trailer: Optional[str] = None
    genres: List[str] = Field(default_factory=list)
    season: Optional[str] = None
    season_year: Optional[int] = None
    starts_at: str = '?-?-?'
    image: Optional[str] = None
    description: str = ''
    airdates: List[Airdate] = Field(default_factory=list)
    characters: List[Character] = Field(default_factory=list)

    @classmethod
    def from_media(cls, media: Media) -> 'Anime':
        airdates = [
            Airdate(episode=edge.node.episode, time=edge.node.airing_at)
            for edge in media.airing_schedule.edges
            if edge.node.episode is not None and edge.node.airing_at is not None
        ]
        characters = [
            Character(
                id=edge.node.id,
                name=edge.node.name.user_preferred,
                image=edge.node.image.large,
                description=edge.node.description
            )
            for edge in media.characters.edges
        ]
        return cls(
            id=media.id,
            name=media.title.preferred,
            episodes=media.episodes or len(airdates) or None,
            trailer=media.trailer.url,
            genres=media.genres,
            season=media.season,
            season_year=media.season_year,
            starts_at=str(media.start_date),
            image=media.cover_image.preferred,
            description=html2md(media.description or ''),
            airdates=airdates,
            characters=characters
        )
