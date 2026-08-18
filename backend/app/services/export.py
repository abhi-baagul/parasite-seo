"""Phase 5 export helpers — HTML / Markdown / TXT / PDF / DOC / CSV."""

from __future__ import annotations

import csv
import io
import re
from html import unescape

import bleach
from bs4 import BeautifulSoup
from fpdf import FPDF
from markdownify import markdownify as html_to_md

from app.storage import safe_filename
from app.utils.html_sanitize import sanitize_html


def build_export_basename(slug: str, title: str) -> str:
    base = slug or title or "article"
    return safe_filename(base.lower().replace(" ", "-"), default="article")


def export_html_document(*, title: str, body_html: str, meta_description: str | None = None) -> str:
    body = sanitize_html(body_html)
    desc = bleach.clean(meta_description or "", tags=[], strip=True)
    safe_title = bleach.clean(title or "Article", tags=[], strip=True)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        f"  <title>{safe_title}</title>\n"
        + (f'  <meta name="description" content="{desc}" />\n' if desc else "")
        + "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "</head>\n"
        "<body>\n"
        f"  <article>\n    <h1>{safe_title}</h1>\n    {body}\n  </article>\n"
        "</body>\n"
        "</html>\n"
    )


def export_markdown(*, title: str, body_html: str) -> str:
    body = sanitize_html(body_html)
    md_body = html_to_md(body, heading_style="ATX", bullets="-")
    return f"# {title.strip() or 'Article'}\n\n{md_body.strip()}\n"


def export_txt(*, title: str, body_html: str) -> str:
    soup = BeautifulSoup(sanitize_html(body_html), "html.parser")
    text = soup.get_text("\n", strip=True)
    text = unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return f"{title.strip() or 'Article'}\n\n{text}\n"


def _pdf_safe(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def export_pdf_bytes(*, title: str, body_html: str) -> bytes:
    """Simple PDF with clickable http(s) links where FPDF supports them."""
    soup = BeautifulSoup(sanitize_html(body_html), "html.parser")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _pdf_safe(title or "Article"))
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)

    for element in soup.find_all(["h1", "h2", "h3", "p", "li", "blockquote", "a"], recursive=True):
        name = element.name
        text = _pdf_safe(element.get_text(" ", strip=True))
        if not text:
            continue
        if name in {"h1", "h2", "h3"}:
            size = {"h1": 14, "h2": 13, "h3": 12}[name]
            pdf.set_font("Helvetica", "B", size)
            pdf.multi_cell(0, 8, text)
            pdf.ln(1)
            pdf.set_font("Helvetica", size=11)
        elif name == "a" and element.get("href", "").startswith(("http://", "https://")):
            href = element["href"]
            pdf.set_text_color(0, 0, 180)
            pdf.write(6, text, href)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(6)
        else:
            pdf.multi_cell(0, 6, text)
            pdf.ln(2)

    if not soup.get_text(strip=True):
        pdf.multi_cell(0, 6, "(Empty article)")

    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()


def export_doc_bytes(*, title: str, body_html: str, meta_description: str | None = None) -> bytes:
    """Word-compatible .doc (HTML in Word XML wrapper). Opens in Microsoft Word / Google Docs."""
    document = export_html_document(title=title, body_html=body_html, meta_description=meta_description)
    wrapper = (
        "<html xmlns:o='urn:schemas-microsoft-com:office:office' "
        "xmlns:w='urn:schemas-microsoft-com:office:word' "
        "xmlns='http://www.w3.org/TR/REC-html40'>\n"
        "<head><meta charset='utf-8' />"
        "<xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml>"
        "</head>\n<body>\n"
        f"{document}\n"
        "</body></html>\n"
    )
    return wrapper.encode("utf-8")


def export_csv_bytes(
    *,
    title: str,
    slug: str,
    body_html: str,
    seo_title: str | None = None,
    meta_description: str | None = None,
    public_url: str | None = None,
    word_count: int | None = None,
    status: str | None = None,
) -> bytes:
    soup = BeautifulSoup(sanitize_html(body_html), "html.parser")
    headings = [
        f"{tag.name.upper()}: {tag.get_text(' ', strip=True)}"
        for tag in soup.find_all(["h1", "h2", "h3"])
        if tag.get_text(strip=True)
    ]
    links = [
        f"{(a.get_text(' ', strip=True) or a.get('href') or '').strip()}|{a.get('href') or ''}"
        for a in soup.find_all("a")
        if a.get("href")
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value"])
    writer.writerow(["title", title or ""])
    writer.writerow(["slug", slug or ""])
    writer.writerow(["public_url", public_url or ""])
    writer.writerow(["seo_title", seo_title or ""])
    writer.writerow(["meta_description", meta_description or ""])
    writer.writerow(["status", status or ""])
    writer.writerow(["word_count", word_count if word_count is not None else ""])
    writer.writerow(["plain_text", soup.get_text(" ", strip=True)])
    for heading in headings:
        writer.writerow(["heading", heading])
    for link in links:
        writer.writerow(["link", link])
    return buffer.getvalue().encode("utf-8")
