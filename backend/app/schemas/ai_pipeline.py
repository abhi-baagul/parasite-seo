from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PromptAnalysisSchema(BaseModel):
    topic: str | None = None
    main_keyword: str | None = None
    secondary_keywords: list[str] = Field(default_factory=list)
    word_count: int | None = Field(default=None, ge=0)
    content_type: str | None = None
    intent: str | None = None
    tone: str | None = None
    audience: str | None = None
    country: str | None = None
    language: str | None = None
    required_headings: list[str] = Field(default_factory=list)
    required_elements: list[str] = Field(default_factory=list)
    cta_requirement: bool | None = None
    offer_information: str | None = None
    promotional_information: str | None = None
    target_url_if_present: str | None = None
    anchor_text_if_present: str | None = None
    media_requirements: list[str] = Field(default_factory=list)
    special_instructions: str | None = None
    uncertain_fields: list[str] = Field(default_factory=list)

    @field_validator(
        "secondary_keywords",
        "required_headings",
        "required_elements",
        "media_requirements",
        "uncertain_fields",
        mode="before",
    )
    @classmethod
    def empty_list_for_none(cls, value):  # noqa: ANN001
        return [] if value is None else value

    @field_validator("cta_requirement", mode="before")
    @classmethod
    def coerce_cta(cls, value):  # noqa: ANN001
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            low = value.strip().lower()
            if low in {"", "null", "none", "unknown", "n/a"}:
                return None
            if low in {"false", "no", "0", "not required"}:
                return False
            return True
        return value

    @field_validator("word_count", mode="before")
    @classmethod
    def coerce_word_count(cls, value):  # noqa: ANN001
        if value is None or isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else None
        return value


class ResearchBriefSchema(BaseModel):
    topic_summary: str = ""
    key_facts: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    subtopics: list[str] = Field(default_factory=list)
    supporting_information: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    claims_requiring_verification: list[str] = Field(default_factory=list)

    @field_validator(
        "key_facts",
        "entities",
        "questions",
        "subtopics",
        "supporting_information",
        "sources",
        "claims_requiring_verification",
        mode="before",
    )
    @classmethod
    def empty_list_for_none(cls, value):  # noqa: ANN001
        return [] if value is None else value

    @field_validator("topic_summary", mode="before")
    @classmethod
    def empty_summary(cls, value):  # noqa: ANN001
        return "" if value is None else value


class ContentStrategySchema(BaseModel):
    content_angle: str = ""
    search_intent: str | None = None
    target_audience: str | None = None
    content_goals: list[str] = Field(default_factory=list)
    recommended_structure: list[str] = Field(default_factory=list)
    key_topics: list[str] = Field(default_factory=list)
    differentiation_opportunities: list[str] = Field(default_factory=list)
    cta_strategy: str | None = None
    internal_link_opportunities: list[str] = Field(default_factory=list)
    external_reference_opportunities: list[str] = Field(default_factory=list)
    media_opportunities: list[str] = Field(default_factory=list)

    @field_validator(
        "content_goals",
        "recommended_structure",
        "key_topics",
        "differentiation_opportunities",
        "internal_link_opportunities",
        "external_reference_opportunities",
        "media_opportunities",
        mode="before",
    )
    @classmethod
    def empty_list_for_none(cls, value):  # noqa: ANN001
        return [] if value is None else value

    @field_validator("content_angle", mode="before")
    @classmethod
    def empty_angle(cls, value):  # noqa: ANN001
        return "" if value is None else value


class OutlineSectionSchema(BaseModel):
    heading: str
    level: int = Field(ge=1, le=3)
    purpose: str | None = None
    notes: str | None = None

    @field_validator("level", mode="before")
    @classmethod
    def coerce_level(cls, value):  # noqa: ANN001
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        if isinstance(value, float):
            return int(value)
        return value


class ContentOutlineSchema(BaseModel):
    h1: str = ""
    sections: list[OutlineSectionSchema] = Field(default_factory=list)

    @field_validator("sections", mode="before")
    @classmethod
    def empty_sections(cls, value):  # noqa: ANN001
        return [] if value is None else value

    @field_validator("h1", mode="before")
    @classmethod
    def empty_h1(cls, value):  # noqa: ANN001
        return "" if value is None else value


class GeneratedArticleSchema(BaseModel):
    title: str
    seo_title: str | None = None
    meta_description: str | None = None
    slug: str
    h1: str | None = None
    html: str
    word_count: int | None = None

    @field_validator("html")
    @classmethod
    def non_empty_html(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Generated HTML cannot be empty")
        return value

    @field_validator("word_count", mode="before")
    @classmethod
    def coerce_word_count(cls, value):  # noqa: ANN001
        if value is None or isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else None
        return value

    @field_validator("slug", mode="before")
    @classmethod
    def coerce_slug(cls, value):  # noqa: ANN001
        if value is None:
            return "article"
        text = str(value).strip().lower().replace(" ", "-")
        return text or "article"


class SeoReportSchema(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    structure_score: int = Field(ge=0, le=100)
    keyword_coverage_score: int = Field(ge=0, le=100)
    readability_score: int = Field(ge=0, le=100)
    intent_score: int = Field(ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class QualityReportSchema(BaseModel):
    score: int = Field(ge=0, le=100)
    status: Literal["passed", "needs_review", "failed"]
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class OptimizationSuggestionSchema(BaseModel):
    before: str
    after: str
    reason: str


class OptimizationReportSchema(BaseModel):
    suggestions: list[OptimizationSuggestionSchema] = Field(default_factory=list)


class AnalyzePromptRequest(BaseModel):
    project_id: str = Field(min_length=1)
    campaign_id: str | None = None
    prompt: str = Field(min_length=1)


class ApproveOutlineRequest(BaseModel):
    outline: ContentOutlineSchema | None = None


class ConfirmRequirementsRequest(BaseModel):
    requirements: PromptAnalysisSchema


class GenerateContentRequest(BaseModel):
    content_id: str
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=256, le=16000)


class OptimizeContentRequest(BaseModel):
    instructions: str | None = None


def dump_schema(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
