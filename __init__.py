from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import traceback
from typing import Any

from aqt import mw
from aqt.operations import QueryOp
from aqt.qt import (
    QAction,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QStandardPaths,
    Qt,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)
from aqt.utils import qconnect, showInfo, showWarning

from .pdf_renderer import render_result_to_pdf
from .scheduler_snapshot import ExportRequest, TomorrowExportResult, build_tomorrow_export


@dataclass(frozen=True)
class ExportJobOutcome:
    result: TomorrowExportResult | None = None
    error_message: str | None = None
    traceback_text: str | None = None


class DeckSelectionDialog(QDialog):
    def __init__(self, parent: Any) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Tomorrow to PDF")
        self.resize(520, 620)

        self._deck_name_by_id: dict[int, str] = {}
        self._deck_tree = QTreeWidget()
        self._deck_tree.setHeaderLabel("Deck scope")
        self._deck_tree.itemChanged.connect(lambda _item, _column: self._update_summary())

        self._include_subdecks = QCheckBox("Include child decks")
        self._include_subdecks.setChecked(True)
        self._include_subdecks.toggled.connect(lambda _checked: self._update_summary())

        self._include_due_cards = QCheckBox("Include due review / learning cards")
        self._include_due_cards.setChecked(True)

        self._include_new_cards = QCheckBox("Include tomorrow's new cards")
        self._include_new_cards.setChecked(True)

        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select the deck scope for tomorrow's printable study plan."))
        layout.addWidget(self._deck_tree, stretch=1)
        layout.addWidget(self._include_subdecks)
        layout.addWidget(self._include_due_cards)
        layout.addWidget(self._include_new_cards)
        layout.addWidget(self._summary_label)
        layout.addWidget(button_box)

        self._populate_deck_tree()
        self._select_current_deck()
        self._update_summary()

    def build_request(self) -> ExportRequest | None:
        selected_ids = self._expanded_selected_deck_ids()
        if not selected_ids:
            return None

        selected_names = tuple(
            sorted((self._deck_name_by_id[deck_id] for deck_id in selected_ids), key=str.casefold)
        )
        return ExportRequest(
            selected_deck_ids=tuple(selected_ids),
            selected_deck_names=selected_names,
            include_subdecks=self._include_subdecks.isChecked(),
            include_due_cards=self._include_due_cards.isChecked(),
            include_new_cards=self._include_new_cards.isChecked(),
            target_study_day=_next_study_day(),
        )

    def _populate_deck_tree(self) -> None:
        nodes_by_path: dict[str, QTreeWidgetItem] = {}
        for deck_id, deck_name in sorted(_deck_entries(), key=lambda item: item[1].casefold()):
            self._deck_name_by_id[deck_id] = deck_name
            path_parts = deck_name.split("::")
            parent_item: QTreeWidgetItem | None = None
            current_path: list[str] = []

            for part in path_parts:
                current_path.append(part)
                path_key = "::".join(current_path)
                item = nodes_by_path.get(path_key)
                if item is None:
                    item = QTreeWidgetItem([part])
                    item.setFlags(
                        item.flags()
                        | Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemIsAutoTristate
                    )
                    item.setCheckState(0, Qt.CheckState.Unchecked)
                    if parent_item is None:
                        self._deck_tree.addTopLevelItem(item)
                    else:
                        parent_item.addChild(item)
                    nodes_by_path[path_key] = item
                parent_item = item

            if parent_item is not None:
                parent_item.setData(0, Qt.ItemDataRole.UserRole, deck_id)
                parent_item.setToolTip(0, deck_name)

        self._deck_tree.expandAll()

    def _select_current_deck(self) -> None:
        current_deck_id = _current_deck_id()
        if current_deck_id is None:
            return
        for item in self._walk_items():
            item_deck_id = item.data(0, Qt.ItemDataRole.UserRole)
            if item_deck_id == current_deck_id:
                item.setCheckState(0, Qt.CheckState.Checked)
                break

    def _walk_items(self) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for index in range(self._deck_tree.topLevelItemCount()):
            top_level = self._deck_tree.topLevelItem(index)
            items.extend(_walk_tree(top_level))
        return items

    def _checked_deck_ids(self) -> set[int]:
        selected: set[int] = set()
        for item in self._walk_items():
            deck_id = item.data(0, Qt.ItemDataRole.UserRole)
            if deck_id is None:
                continue
            if item.checkState(0) == Qt.CheckState.Checked:
                selected.add(int(deck_id))
        return selected

    def _expanded_selected_deck_ids(self) -> tuple[int, ...]:
        selected_ids = self._checked_deck_ids()
        if not selected_ids:
            return ()
        if not self._include_subdecks.isChecked():
            return tuple(sorted(selected_ids))

        prefixes = [f"{self._deck_name_by_id[deck_id]}::" for deck_id in selected_ids]
        expanded = set(selected_ids)
        for deck_id, deck_name in self._deck_name_by_id.items():
            if any(deck_name.startswith(prefix) for prefix in prefixes):
                expanded.add(deck_id)
        return tuple(sorted(expanded))

    def _update_summary(self) -> None:
        selected_ids = self._expanded_selected_deck_ids()
        if not selected_ids:
            self._summary_label.setText("No deck selected.")
            return

        approx_cards = _count_cards_in_scope(selected_ids)
        self._summary_label.setText(
            f"Selected decks: {len(selected_ids)}. Approx cards in scope: {approx_cards}. "
            "Exact tomorrow order and count are computed during export."
        )


def _walk_tree(item: QTreeWidgetItem) -> list[QTreeWidgetItem]:
    items = [item]
    for child_index in range(item.childCount()):
        items.extend(_walk_tree(item.child(child_index)))
    return items


def _deck_entries() -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    all_names_and_ids = getattr(mw.col.decks, "all_names_and_ids", None)
    if not callable(all_names_and_ids):
        return result

    for entry in all_names_and_ids():
        deck_id = _coerce_int(entry.get("id") if isinstance(entry, dict) else getattr(entry, "id", None))
        deck_name = entry.get("name") if isinstance(entry, dict) else getattr(entry, "name", None)
        if deck_id is None or deck_name is None:
            continue
        result.append((deck_id, str(deck_name)))
    return result


def _current_deck_id() -> int | None:
    current = getattr(mw.col.decks, "current", None)
    if not callable(current):
        return None
    try:
        deck = current()
    except Exception:
        return None

    if isinstance(deck, dict):
        return _coerce_int(deck.get("id"))
    return _coerce_int(getattr(deck, "id", None))


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _count_cards_in_scope(deck_ids: tuple[int, ...]) -> int:
    placeholders = ",".join("?" for _ in deck_ids)
    return int(
        mw.col.db.scalar(
            f"select count(*) from cards where did in ({placeholders})",
            *deck_ids,
        )
        or 0
    )


def _default_output_path() -> str:
    target_day = _next_study_day()
    base_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
    filename = f"anki-tomorrow-{target_day.strftime('%Y-%m-%d')}.pdf"
    return str(base_dir) + "/" + filename if base_dir else filename


def _next_study_day() -> datetime:
    for attr_name in ("day_cutoff", "dayCutoff"):
        cutoff = getattr(mw.col.sched, attr_name, None)
        if cutoff:
            try:
                return datetime.fromtimestamp(int(cutoff)).astimezone()
            except Exception:
                pass
    return datetime.now().astimezone() + timedelta(days=1)


def _run_export_job(collection_path: str, request: ExportRequest) -> ExportJobOutcome:
    try:
        result = build_tomorrow_export(collection_path, request)
        return ExportJobOutcome(result=result)
    except Exception as exc:
        return ExportJobOutcome(
            error_message=str(exc),
            traceback_text=traceback.format_exc(),
        )


def _start_export() -> None:
    dialog = DeckSelectionDialog(mw)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    request = dialog.build_request()
    if request is None:
        showWarning("Select at least one deck before exporting.")
        return
    if not request.include_due_cards and not request.include_new_cards:
        showWarning("Select at least one card type to export.")
        return

    output_path, _selected_filter = QFileDialog.getSaveFileName(
        mw,
        "Export Tomorrow to PDF",
        _default_output_path(),
        "PDF Files (*.pdf)",
    )
    if not output_path:
        return
    if not output_path.lower().endswith(".pdf"):
        output_path = f"{output_path}.pdf"

    collection_path = mw.col.path
    mw.progress.start(label="Preparing tomorrow queue...", immediate=True)

    def on_export_finished(outcome: ExportJobOutcome) -> None:
        mw.progress.finish()

        if outcome.error_message:
            details = outcome.traceback_text or outcome.error_message
            showWarning(f"Export failed.\n\n{details}")
            return
        if outcome.result is None:
            showWarning("Export finished without a result.")
            return

        mw.progress.start(label="Rendering PDF...", immediate=True)
        try:
            render_result_to_pdf(outcome.result, output_path)
        except Exception:
            mw.progress.finish()
            showWarning(f"PDF rendering failed.\n\n{traceback.format_exc()}")
            return
        mw.progress.finish()

        showInfo(
            "Tomorrow study PDF exported.\n\n"
            f"Cards: {len(outcome.result.cards)}\n"
            f"Path: {output_path}"
        )

    QueryOp(
        parent=mw,
        op=lambda *_args: _run_export_job(collection_path, request),
        success=on_export_finished,
    ).without_collection().run_in_background()


action = QAction("Export Tomorrow to PDF", mw)
qconnect(action.triggered, _start_export)
mw.form.menuTools.addAction(action)
