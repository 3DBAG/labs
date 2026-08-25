"""Generate the 3DBAG Labs card grid from the repository content catalogue."""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from properdocs.exceptions import ProperDocsException


ROOT = Path(__file__).resolve().parent
DOCS = (ROOT / "docs").resolve()
CATALOGUE = ROOT / "labs-content.json"
REQUIRED_FIELDS = {
    "id",
    "date_added",
    "title",
    "description",
    "link",
    "image",
    "authors",
    "contact",
    "in_3dbag",
    "archived",
}


def _error(index: int, message: str) -> ProperDocsException:
    return ProperDocsException(f"labs-content.json record {index}: {message}")


def _image_path(value: Any, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(index, "'image' must be a non-empty string")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise _error(index, "'image' must be a relative path inside docs/")
    if any(part == ".." for part in (*posix.parts, *windows.parts)):
        raise _error(index, "'image' must not contain path traversal ('..')")
    candidate = (DOCS / Path(*posix.parts)).resolve()
    try:
        candidate.relative_to(DOCS)
    except ValueError as exc:
        raise _error(index, "'image' must resolve inside docs/") from exc
    if not candidate.is_file():
        raise _error(index, f"image does not exist: {value}")
    return value.replace("\\", "/")


def _load_cards() -> list[dict[str, Any]]:
    try:
        records = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProperDocsException(f"Unable to read labs-content.json: {exc}") from exc
    if not isinstance(records, list):
        raise ProperDocsException("labs-content.json must contain a JSON array")

    cards = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise _error(index, "must be a JSON object")
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            raise _error(index, f"missing required field(s): {', '.join(sorted(missing))}")
        if not isinstance(record["id"], int) or isinstance(record["id"], bool):
            raise _error(index, "'id' must be an integer")
        for field in ("title", "description", "link", "contact", "date_added"):
            if not isinstance(record[field], str):
                raise _error(index, f"'{field}' must be a string")
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record["date_added"]):
                raise ValueError
            date.fromisoformat(record["date_added"])
        except ValueError as exc:
            raise _error(index, "'date_added' must be an ISO date (YYYY-MM-DD)") from exc
        if (
            not isinstance(record["authors"], list)
            or not record["authors"]
            or any(not isinstance(author, str) for author in record["authors"])
        ):
            raise _error(index, "'authors' must be a non-empty list of strings")
        for field in ("in_3dbag", "archived"):
            if not isinstance(record[field], bool):
                raise _error(index, f"'{field}' must be a boolean")
        card = dict(record)
        card["image"] = _image_path(record["image"], index)
        cards.append(card)
    return cards


def _cards_markdown(cards: list[dict[str, Any]]) -> str:
    output = ['<div class="grid cards labs-grid" markdown>']
    for card in cards:
        esc = lambda value: html.escape(str(value), quote=True)
        authors = ", ".join(esc(author) for author in card["authors"])
        output.extend(
            [
                '<div class="card lab-card" markdown>',
                f'<img class="lab-card__image" src="{esc(card["image"])}" alt="{esc(card["title"])}" />',
                f'<h2>{esc(card["title"])}</h2>',
                f'<p>{esc(card["description"])}</p>',
                '<div class="lab-card__metadata">',
                '<div class="lab-card__meta-row">',
                f'<span><strong>Date added:</strong> {esc(card["date_added"])}</span>',
                f'<span><strong>Authors:</strong> {authors}</span>',
                f'<span><strong>Contact:</strong> <a href="mailto:{esc(card["contact"])}">{esc(card["contact"])}</a></span>',
                '</div>',
                '<div class="lab-card__status-row">',
                '<span class="lab-card__badge lab-card__badge--in-3dbag">In 3DBAG</span>'
                if card["in_3dbag"]
                else '',
                '<span class="lab-card__badge lab-card__badge--archived">Archived</span>'
                if card["archived"]
                else '',
                '</div>',
                '</div>',
                f'<p><a class="md-button" href="{esc(card["link"])}">Visit</a></p>',
                '</div>',
            ]
        )
    output.append("</div>")
    return "\n".join(output)


def on_page_markdown(markdown: str, page: Any, config: Any, files: Any) -> str:
    if page.file.src_uri != "index.md":
        return markdown
    marker = "<!-- labs-cards -->"
    if marker not in markdown:
        raise ProperDocsException("docs/index.md is missing the <!-- labs-cards --> marker")
    return markdown.replace(marker, _cards_markdown(_load_cards()))
