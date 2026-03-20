from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import re
import sqlite3
import tempfile
import time
from typing import Any, Iterable

from anki.cards import Card
from anki.collection import Collection

SECONDS_PER_DAY = 24 * 60 * 60
ANSWER_SPLIT_RE = re.compile(r"<hr\b[^>]*id=['\"]?answer['\"]?[^>]*>", re.IGNORECASE)


@dataclass(frozen=True)
class ExportRequest:
    selected_deck_ids: tuple[int, ...]
    selected_deck_names: tuple[str, ...]
    include_subdecks: bool
    include_due_cards: bool
    include_new_cards: bool
    page_size: str = "A4"
    target_study_day: datetime | None = None


@dataclass(frozen=True)
class QueuedCardForPdf:
    position: int
    card_id: int
    note_id: int
    notetype_id: int
    deck_id: int
    card_ord: int
    deck_name: str
    template_name: str
    card_kind: str
    front_html: str
    back_html: str


@dataclass(frozen=True)
class TomorrowExportResult:
    cards: tuple[QueuedCardForPdf, ...]
    generated_at: datetime
    target_study_day: datetime
    selected_deck_names: tuple[str, ...]
    page_size: str


def build_tomorrow_export(
    source_collection_path: str,
    request: ExportRequest,
) -> TomorrowExportResult:
    generated_at = datetime.now().astimezone()
    target_study_day = request.target_study_day or (generated_at + timedelta(days=1))

    with tempfile.TemporaryDirectory(prefix="anki-tomorrow-pdf-") as temp_dir:
        temp_collection_path = os.path.join(
            temp_dir,
            os.path.basename(source_collection_path),
        )
        _create_sqlite_snapshot(source_collection_path, temp_collection_path)

        temp_col = Collection(temp_collection_path)
        try:
            _configure_active_decks(temp_col, request.selected_deck_ids)
            _shift_collection_to_tomorrow(temp_col)
            _reset_scheduler_if_possible(temp_col)
            cards = _collect_cards_for_export(temp_col, request)
        finally:
            temp_col.close()

    return TomorrowExportResult(
        cards=tuple(cards),
        generated_at=generated_at,
        target_study_day=target_study_day,
        selected_deck_names=request.selected_deck_names,
        page_size=request.page_size,
    )


def _create_sqlite_snapshot(source_path: str, destination_path: str) -> None:
    def unicase(left: str | None, right: str | None) -> int:
        left_value = (left or "").casefold()
        right_value = (right or "").casefold()
        if left_value < right_value:
            return -1
        if left_value > right_value:
            return 1
        return 0

    source_uri = f"file:{source_path}?mode=ro"
    source = sqlite3.connect(source_uri, uri=True)
    destination = sqlite3.connect(destination_path)
    try:
        source.create_collation("unicase", unicase)
        source.execute("pragma busy_timeout = 5000")
        destination.execute("pragma busy_timeout = 5000")
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def _configure_active_decks(col: Collection, selected_deck_ids: Iterable[int]) -> None:
    ordered_ids = sorted({int(deck_id) for deck_id in selected_deck_ids})
    if not ordered_ids:
        raise ValueError("No deck IDs were provided for export.")

    conf = getattr(col, "conf", None)
    if isinstance(conf, dict):
        conf["curDeck"] = ordered_ids[0]
        conf["activeDecks"] = ordered_ids

    if hasattr(col, "set_config"):
        try:
            col.set_config("curDeck", ordered_ids[0])
            col.set_config("activeDecks", ordered_ids)
        except Exception:
            pass


def _shift_collection_to_tomorrow(col: Collection) -> None:
    def shift() -> None:
        # Review/day-learning due numbers are relative to collection creation day,
        # so moving `crt` back by one day makes tomorrow's queue due "today".
        col.db.execute("update col set crt = crt - ?", SECONDS_PER_DAY)

        # Intraday learning cards use absolute timestamps in seconds.
        col.db.execute(
            "update cards set due = due - ? where queue = 1",
            SECONDS_PER_DAY,
        )

    if hasattr(col.db, "transact"):
        col.db.transact(shift)
    else:
        shift()


def _reset_scheduler_if_possible(col: Collection) -> None:
    sched = col.sched
    if hasattr(sched, "reset"):
        try:
            sched.reset()
        except Exception:
            pass


def _collect_cards_for_export(
    col: Collection,
    request: ExportRequest,
) -> list[QueuedCardForPdf]:
    queued_cards = _collect_cards_from_scheduler(col, request)
    if queued_cards:
        return queued_cards
    return _collect_cards_from_manual_fallback(col, request)


def _collect_cards_from_scheduler(
    col: Collection,
    request: ExportRequest,
) -> list[QueuedCardForPdf]:
    sched = getattr(col, "sched", None)
    if sched is None or not hasattr(sched, "get_queued_cards"):
        return []

    total_cards = int(col.db.scalar("select count(*) from cards") or 0)
    get_queued_cards = getattr(sched, "get_queued_cards")

    try:
        raw_queue = get_queued_cards(fetch_limit=total_cards + 1024)
    except TypeError:
        try:
            raw_queue = get_queued_cards(total_cards + 1024)
        except TypeError:
            raw_queue = get_queued_cards()

    deck_names = _deck_name_map(col)
    selected_deck_ids = set(request.selected_deck_ids)
    seen_card_ids: set[int] = set()
    exported_cards: list[QueuedCardForPdf] = []

    for entry in _queued_entries(raw_queue):
        card = _resolve_queue_entry_to_card(col, entry)
        if card is None:
            continue

        deck_id = _card_deck_id(card)
        if deck_id not in selected_deck_ids:
            continue

        card_kind = _card_kind(card)
        if card_kind == "new" and not request.include_new_cards:
            continue
        if card_kind != "new" and not request.include_due_cards:
            continue
        if card.id in seen_card_ids:
            continue

        seen_card_ids.add(card.id)
        exported_cards.append(
            _queued_card_from_card(
                col=col,
                card=card,
                deck_names=deck_names,
                position=len(exported_cards) + 1,
            )
        )

    return exported_cards


def _queued_entries(raw_queue: Any) -> Iterable[Any]:
    if raw_queue is None:
        return []
    if isinstance(raw_queue, (list, tuple)):
        return raw_queue
    cards_attr = getattr(raw_queue, "cards", None)
    if cards_attr is not None:
        return cards_attr
    queued_attr = getattr(raw_queue, "queued_cards", None)
    if queued_attr is not None:
        return queued_attr
    return [raw_queue]


def _resolve_queue_entry_to_card(col: Collection, entry: Any) -> Card | None:
    if isinstance(entry, Card):
        return entry

    entry_card = getattr(entry, "card", None)
    if isinstance(entry_card, Card):
        return entry_card
    if entry_card is not None:
        card_id = getattr(entry_card, "id", None) or getattr(entry_card, "card_id", None)
        if card_id is not None:
            return col.get_card(int(card_id))

    for attr_name in ("card_id", "cid", "id"):
        card_id = getattr(entry, attr_name, None)
        if card_id is not None:
            try:
                return col.get_card(int(card_id))
            except Exception:
                continue

    if isinstance(entry, int):
        try:
            return col.get_card(entry)
        except Exception:
            return None

    return None


def _collect_cards_from_manual_fallback(
    col: Collection,
    request: ExportRequest,
) -> list[QueuedCardForPdf]:
    selected_deck_ids = tuple(sorted(set(request.selected_deck_ids)))
    placeholders = ",".join("?" for _ in selected_deck_ids)
    deck_names = _deck_name_map(col)
    current_day = _current_sched_day(col)
    now_ts = int(time.time())

    where_clauses: list[str] = []
    params: list[int] = list(selected_deck_ids)

    if request.include_due_cards:
        where_clauses.extend(
            [
                "(queue = 1 and due <= ?)",
                "(queue = 3 and due <= ?)",
                "(queue = 2 and due <= ?)",
            ]
        )
        params.extend([now_ts, current_day, current_day])

    if request.include_new_cards:
        where_clauses.append("(queue = 0)")

    if not where_clauses:
        return []

    sql = f"""
        select id
        from cards
        where did in ({placeholders})
          and ({' or '.join(where_clauses)})
        order by
          case
            when queue = 1 then 0
            when queue = 3 then 1
            when queue = 2 then 2
            else 3
          end,
          due,
          ord,
          id
    """
    rows = col.db.list(sql, *params)

    exported_cards: list[QueuedCardForPdf] = []
    seen_card_ids: set[int] = set()
    for card_id in rows:
        card = col.get_card(card_id)
        if card.id in seen_card_ids:
            continue
        seen_card_ids.add(card.id)
        exported_cards.append(
            _queued_card_from_card(
                col=col,
                card=card,
                deck_names=deck_names,
                position=len(exported_cards) + 1,
            )
        )

    return exported_cards


def _current_sched_day(col: Collection) -> int:
    sched_today = getattr(col.sched, "today", None)
    if isinstance(sched_today, int):
        return sched_today

    crt = int(col.db.scalar("select crt from col"))
    return int((time.time() - crt) // SECONDS_PER_DAY)


def _queued_card_from_card(
    col: Collection,
    card: Card,
    deck_names: dict[int, str],
    position: int,
) -> QueuedCardForPdf:
    deck_id = _card_deck_id(card)
    template_name = _template_name(card)
    deck_name = deck_names.get(deck_id, f"Deck {deck_id}")

    return QueuedCardForPdf(
        position=position,
        card_id=int(card.id),
        note_id=int(card.nid),
        notetype_id=int(card.note().mid),
        deck_id=deck_id,
        card_ord=int(card.ord),
        deck_name=deck_name,
        template_name=template_name,
        card_kind=_card_kind(card),
        front_html=_prepare_front_html(card),
        back_html=_prepare_back_html(card),
    )


def _card_deck_id(card: Card) -> int:
    original_deck_id = getattr(card, "odid", 0) or 0
    return int(original_deck_id or card.did)


def _template_name(card: Card) -> str:
    try:
        template = card.template()
    except Exception:
        return ""
    if isinstance(template, dict):
        return str(template.get("name", ""))
    return str(getattr(template, "name", ""))


def _card_kind(card: Card) -> str:
    queue = int(getattr(card, "queue", 0))
    card_type = int(getattr(card, "type", 0))
    if queue == 0 or card_type == 0:
        return "new"
    if queue in (1, 3) or card_type in (1, 3):
        return "learning"
    return "review"


def _prepare_front_html(card: Card) -> str:
    return _sanitize_rendered_html(card.question(reload=True))


def _prepare_back_html(card: Card) -> str:
    answer_html = card.answer()
    chunks = ANSWER_SPLIT_RE.split(answer_html, maxsplit=1)
    if len(chunks) == 2:
        answer_html = chunks[1]
    return _sanitize_rendered_html(answer_html)


def _sanitize_rendered_html(html: str) -> str:
    return (html or "").strip()


def _deck_name_map(col: Collection) -> dict[int, str]:
    result: dict[int, str] = {}
    all_names_and_ids = getattr(col.decks, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        for entry in all_names_and_ids():
            deck_id, deck_name = _deck_id_and_name(entry)
            if deck_id is not None and deck_name is not None:
                result[deck_id] = deck_name

    name_lookup = getattr(col.decks, "name", None)
    if callable(name_lookup):
        for deck_id in list(result):
            try:
                result[deck_id] = str(name_lookup(deck_id))
            except Exception:
                pass

    return result


def _deck_id_and_name(entry: Any) -> tuple[int | None, str | None]:
    if isinstance(entry, dict):
        deck_id = entry.get("id")
        deck_name = entry.get("name")
        return _coerce_int(deck_id), _coerce_str(deck_name)

    deck_id = getattr(entry, "id", None)
    deck_name = getattr(entry, "name", None)
    return _coerce_int(deck_id), _coerce_str(deck_name)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
