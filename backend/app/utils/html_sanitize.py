import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "h1",
    "h2",
    "h3",
    "h4",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "a",
    "blockquote",
    "code",
    "pre",
    "div",
    "span",
    "section",
    "figure",
    "figcaption",
    "img",
    "hr",
    "iframe",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target", "class"],
    "div": ["class", "data-cta"],
    "span": ["class"],
    "section": ["class", "data-cta"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "iframe": ["src", "title", "width", "height", "allow", "allowfullscreen", "frameborder", "loading"],
    "figure": ["class"],
}


def sanitize_html(value: str) -> str:
    cleaned = bleach.clean(
        value or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    # Drop javascript: that bleach might leave in edge cases via malformed attrs — bleach handles protocols.
    return cleaned


def count_words(html: str) -> int:
    text = bleach.clean(html or "", tags=[], strip=True)
    return len([part for part in text.split() if part])


def count_characters(html: str) -> int:
    text = bleach.clean(html or "", tags=[], strip=True)
    return len(text)


def reading_time_minutes(html: str, *, wpm: int = 200) -> int:
    words = count_words(html)
    return max(1, (words + wpm - 1) // wpm) if words else 0
