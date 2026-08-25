"""Generate the 3DBAG Labs card grid from the repository content catalogue."""

from __future__ import annotations

import html
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from PIL import Image, UnidentifiedImageError
from jsonschema import Draft202012Validator, FormatChecker
from properdocs.exceptions import ProperDocsException


ROOT = Path(__file__).resolve().parent
DOCS = (ROOT / "docs").resolve()
CATALOGUE = ROOT / "labs-content.json"
SCHEMA = ROOT / "labs-content.schema.json"


def _error(index: int, message: str) -> ProperDocsException:
    return ProperDocsException(f"labs-content.json record {index}: {message}")


def _image_path(value: Any, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(index, "'image' must be a non-empty string")
    normalized = value.replace("\\", "/")
    posix = PurePosixPath(normalized)
    windows = PureWindowsPath(normalized)
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
    return normalized


def _validate_image_dimensions(path: str, index: int) -> None:
    image_path = DOCS / Path(*PurePosixPath(path).parts)
    try:
        with Image.open(image_path) as image:
            width, height = image.size
    except (OSError, UnidentifiedImageError) as exc:
        raise _error(index, f"image '{path}' is not a readable image: {exc}") from exc
    if (width, height) != (600, 350):
        raise _error(
            index,
            f"image '{path}' has dimensions {width}x{height}; expected exactly 600x350 pixels",
        )


def _word_count(value: str) -> int:
    return len(value.split())


def _validate_schema(records: Any) -> None:
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProperDocsException(f"Unable to read labs-content.schema.json: {exc}") from exc

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(records), key=lambda error: list(error.absolute_path))
    messages = []
    for error in errors:
        if error.absolute_path and isinstance(error.absolute_path[0], int):
            index = error.absolute_path[0] + 1
            path = ".".join(str(part) for part in list(error.absolute_path)[1:])
            location = f"'{path}'" if path else "record"
            messages.append(str(_error(index, f"{location} {error.message}")))
        else:
            messages.append(f"labs-content.json: {error.message}")
    if messages:
        raise ProperDocsException("\n".join(messages))


def _load_cards() -> list[dict[str, Any]]:
    try:
        records = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProperDocsException(f"Unable to read labs-content.json: {exc}") from exc
    _validate_schema(records)

    errors = []
    seen_ids: dict[int, int] = {}
    cards = []
    for index, record in enumerate(records, start=1):
        record_id = record["id"]
        if record_id in seen_ids:
            errors.append(
                _error(
                    index,
                    f"'id' {record_id} duplicates the value from record {seen_ids[record_id]}",
                )
            )
        else:
            seen_ids[record_id] = index
        if _word_count(record["description"]) > 140:
            errors.append(_error(index, "'description' must contain no more than 140 words"))
        card = dict(record)
        try:
            card["image"] = _image_path(record["image"], index)
            _validate_image_dimensions(card["image"], index)
        except ProperDocsException as exc:
            errors.append(exc)
        cards.append(card)
    if errors:
        raise ProperDocsException("\n".join(str(error) for error in errors))
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
                f'<span><strong>Authors:</strong> {authors}</span>',
                f'<span><strong>Contact:</strong> <a href="mailto:{esc(card["contact"])}">{esc(card["contact"])}</a></span>',
                f'<span><strong>Date added:</strong> {esc(card["date_added"])}</span>',
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
