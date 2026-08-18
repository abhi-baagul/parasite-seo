"""Phase 4 enrichment request/response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class TitleOptionSchema(BaseModel):
    title: str
    character_count: int | None = None
    keyword_position: str | None = None
    clarity_score: int | None = Field(default=None, ge=0, le=100)
    intent_match: int | None = Field(default=None, ge=0, le=100)


class MetaOptionSchema(BaseModel):
    meta_description: str
    character_count: int | None = None
    primary_keyword_present: bool | None = None
    cta_presence: bool | None = None


class MetadataPackageSchema(BaseModel):
    title_options: list[TitleOptionSchema] = Field(default_factory=list)
    meta_options: list[MetaOptionSchema] = Field(default_factory=list)
    slug: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None


class TagsCategoriesSchema(BaseModel):
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class MediaPlanItemSchema(BaseModel):
    media_type: Literal["image", "video", "diagram", "infographic"] = "image"
    placement: str | None = None
    purpose: str | None = None
    description: str | None = None
    generation_prompt: str | None = None
    alt_text: str | None = None
    caption: str | None = None
    suggested_filename: str | None = None


class MediaPlanSchema(BaseModel):
    items: list[MediaPlanItemSchema] = Field(default_factory=list)
    video_suggestions: list[MediaPlanItemSchema] = Field(default_factory=list)


class SelectMetadataRequest(BaseModel):
    seo_title: str | None = None
    meta_description: str | None = None
    slug: str | None = None
    canonical_url: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None


class SuggestionDecisionRequest(BaseModel):
    status: Literal["approved", "rejected", "inserted"]


class ExternalReferenceDecisionRequest(BaseModel):
    status: Literal["approved", "rejected", "inserted"]
    url: str | None = None


class InsertLinkRequest(BaseModel):
    link_id: str | None = None
    target_url: str
    anchor_text: str = Field(min_length=1, max_length=500)
    link_attribute: Literal["standard", "sponsored", "ugc", "nofollow"] = "standard"
    placement_phrase: str | None = None


class TargetLinkSuggestRequest(BaseModel):
    target_url: str
    anchor_text: str = Field(min_length=1, max_length=500)
    link_attribute: Literal["standard", "sponsored", "ugc", "nofollow"] = "standard"


class ExternalReferenceCreate(BaseModel):
    url: str | None = None
    anchor_suggestion: str
    reason: str | None = None
    source_type: str = "reference"
    requires_verification: bool = True


def dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
