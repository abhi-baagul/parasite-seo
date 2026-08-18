from app.models.content import ContentAsset, ContentLink
from app.models.prompt import Prompt
from app.repositories.base import BaseRepository


class PromptRepository(BaseRepository[Prompt]):
    model = Prompt


class ContentAssetRepository(BaseRepository[ContentAsset]):
    model = ContentAsset


class ContentLinkRepository(BaseRepository[ContentLink]):
    model = ContentLink
