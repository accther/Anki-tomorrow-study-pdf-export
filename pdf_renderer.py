from __future__ import annotations

from html import escape
from typing import Callable

from anki.latex import render_latex
from aqt import mw
from aqt.qt import QEventLoop, QMarginsF, QPageLayout, QPageSize, QTimer
from aqt.theme import theme_manager
from aqt.webview import AnkiWebView

from .scheduler_snapshot import QueuedCardForPdf, TomorrowExportResult


def render_result_to_pdf(
    result: TomorrowExportResult,
    output_path: str,
) -> None:
    web = AnkiWebView(parent=mw)
    web.resize(1, 1)
    web.move(-10000, -10000)

    page = web.page()
    layout = QPageLayout(
        QPageSize(_page_size_id(result.page_size)),
        QPageLayout.Orientation.Portrait,
        QMarginsF(12, 14, 12, 14),
    )
    state: dict[str, str | None] = {"error": None}
    event_loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)

    def cleanup() -> None:
        timeout.stop()
        try:
            page.pdfPrintingFinished.disconnect(on_pdf_finished)
        except Exception:
            pass
        web.deleteLater()

    def finish_with_error(message: str) -> None:
        state["error"] = message
        cleanup()
        event_loop.quit()

    def on_pdf_finished(path: str, success: bool) -> None:
        if not success:
            finish_with_error(f"Web rendering failed while writing PDF: {path}")
            return
        cleanup()
        event_loop.quit()

    def on_bridge_command(cmd: str) -> None:
        if cmd == "tomorrow-pdf-ready":
            try:
                page.printToPdf(output_path, layout)
            except TypeError:
                page.printToPdf(output_path)
            return
        if cmd.startswith("tomorrow-pdf-error:"):
            finish_with_error(cmd.split(":", 1)[1])

    timeout.timeout.connect(lambda: finish_with_error("Timed out while waiting for MathJax rendering."))
    page.pdfPrintingFinished.connect(on_pdf_finished)
    web.set_bridge_command(on_bridge_command, web)

    body = _build_export_body(result)
    web.stdHtml(
        body,
        css=["css/reviewer.css"],
        js=[
            "js/webview.js",
            "js/vendor/jquery.min.js",
            "js/mathjax.js",
            "js/vendor/mathjax/tex-chtml-full.js",
        ],
        head=_build_export_head(result),
        context=mw,
        default_css=True,
    )
    web.eval(_mathjax_ready_script())
    timeout.start(20000)
    event_loop.exec()

    if state["error"]:
        raise RuntimeError(state["error"])


def _page_size_id(page_size: str) -> QPageSize.PageSizeId:
    normalized = (page_size or "").strip().upper()
    if normalized == "LETTER":
        return QPageSize.PageSizeId.Letter
    return QPageSize.PageSizeId.A4


def _build_export_head(result: TomorrowExportResult) -> str:
    return f"""
<style>
  @page {{
    size: {escape(result.page_size)};
    margin: 14mm 12mm;
  }}

  html,
  body,
  html.night-mode,
  html.night-mode body,
  body.nightMode,
  body.night_mode {{
    background: #ffffff;
    color: #1f2933;
    font-family: "Helvetica Neue", "PingFang SC", sans-serif;
    font-size: 13.5pt;
    line-height: 1.75;
    margin: 0;
    padding: 0;
  }}

  h1, h2, h3, p {{
    margin: 0;
  }}

  .cover {{
    border-bottom: 1px solid #d5dbe3;
    margin-bottom: 9mm;
    padding-bottom: 4mm;
  }}

  .cover h1 {{
    font-size: 20pt;
    margin-bottom: 2.5mm;
  }}

  .meta {{
    color: #52606d;
    display: flex;
    font-size: 11pt;
    gap: 4mm;
  }}

  .section-title {{
    font-size: 15pt;
    margin: 8mm 0 5mm;
  }}

  .page {{
    page-break-after: always;
  }}

  .page:last-of-type {{
    page-break-after: auto;
  }}

  .print-card-block {{
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 3px;
    break-inside: avoid;
    margin-bottom: 5mm;
    padding: 4mm 4.5mm 4.5mm;
  }}

  .print-card-block:last-child {{
    margin-bottom: 0;
  }}

  .print-card-header {{
    align-items: baseline;
    color: #102a43;
    display: flex;
    justify-content: space-between;
    font-size: 13.5pt;
    font-weight: 700;
    line-height: 1.75;
    margin-bottom: 3mm;
  }}

  .print-card-title {{
    display: inline-flex;
    gap: 2.5mm;
    align-items: center;
  }}

  .kind-pill {{
    border: 1px solid #bcccdc;
    border-radius: 999px;
    color: #486581;
    font-size: 10.5pt;
    font-weight: 700;
    line-height: 1.2;
    padding: 1mm 2.5mm;
    white-space: nowrap;
  }}

  .print-card-body {{
    background: #ffffff;
    font-size: 13.5pt;
    line-height: 1.75;
    word-wrap: break-word;
  }}

  .print-card-body img {{
    max-width: 100%;
    vertical-align: middle;
  }}

  .print-card-body .card {{
    background: #ffffff !important;
    color: #1f2933 !important;
    font-size: inherit;
    line-height: 1.75;
  }}

  .print-card-body .MathJax,
  .print-card-body mjx-container {{
    font-size: 1em !important;
  }}

  .response-strip {{
    display: grid;
    gap: 2mm;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    margin-top: 5mm;
  }}

  .response-option {{
    color: #243b53;
    font-size: 10pt;
    font-weight: 700;
    line-height: 1.4;
    padding: 0.8mm 1mm;
    text-align: center;
  }}

  .workspace {{
    border-top: 1px dashed #bcccdc;
    margin-top: 5mm;
    min-height: 28mm;
    padding-top: 3mm;
  }}

  .answers .print-card-body {{
    color: #243b53;
  }}

  body.nightMode .latex,
  body.night_mode .latex {{
    filter: none !important;
  }}

  .appendix-title {{
    page-break-before: always;
  }}

  .empty-state {{
    border: 1px dashed #9fb3c8;
    color: #52606d;
    padding: 8mm;
  }}
</style>
"""


def _build_export_body(result: TomorrowExportResult) -> str:
    title = "Tomorrow Study Export"
    study_date = result.target_study_day.strftime("%Y-%m-%d")
    total_cards = len(result.cards)

    prompt_blocks = _grouped_pages(result.cards, _prompt_section, "questions")
    answer_blocks = _grouped_pages(result.cards, _answer_section, "answers")
    empty_state = (
        "<section class='empty-state'><p>No cards were scheduled for the selected decks.</p></section>"
        if not result.cards
        else ""
    )

    return f"""
<section class="cover">
  <h1>{escape(title)}</h1>
  <div class="meta">
    <p><strong>Study day:</strong> {escape(study_date)}</p>
    <p><strong>Total cards:</strong> {total_cards}</p>
  </div>
</section>

<section class="prompts">
  <h2 class="section-title">Questions</h2>
  {empty_state}
  {prompt_blocks}
</section>

<section class="answers">
  <h2 class="section-title appendix-title">Answers</h2>
  {answer_blocks}
</section>
"""


def _grouped_pages(
    cards: tuple[QueuedCardForPdf, ...],
    renderer: Callable[[QueuedCardForPdf], str],
    section_name: str,
) -> str:
    if not cards:
        return ""

    pages: list[str] = []
    for start in range(0, len(cards), 10):
        page_cards = cards[start : start + 10]
        blocks = "".join(renderer(card) for card in page_cards)
        pages.append(f"<section class=\"page {escape(section_name)}\">{blocks}</section>")
    return "".join(pages)


def _prompt_section(card: QueuedCardForPdf) -> str:
    return _card_section(card, card.front_html, "Question")


def _answer_section(card: QueuedCardForPdf) -> str:
    return _card_section(card, card.back_html, "Answer")


def _card_section(card: QueuedCardForPdf, body_html: str, label: str) -> str:
    prepared_html = _prepare_html_for_pdf(card, body_html)
    body_class = theme_manager.body_classes_for_card_ord(card.card_ord, False)
    kind_label = _kind_label(card.card_kind)
    response_strip = _response_strip() if label == "Question" else ""
    workspace = "<div class=\"workspace\"></div>" if label == "Question" else ""
    return f"""
<section class="print-card-block">
  <div class="print-card-header">
    <span class="print-card-title">
      <span>{escape(label)} {card.position}</span>
      <span class="kind-pill">{escape(kind_label)}</span>
    </span>
  </div>
  <div class="print-card-body">
    <div class="{escape(body_class)}">
      {prepared_html}
    </div>
    {response_strip}
    {workspace}
  </div>
</section>
"""


def _prepare_html_for_pdf(card: QueuedCardForPdf, html: str) -> str:
    if mw and mw.col:
        model = mw.col.models.get(card.notetype_id)
        if model:
            html = render_latex(html, model, mw.col)
        return mw.prepare_card_text_for_display(html)
    return html


def _kind_label(card_kind: str) -> str:
    return {
        "new": "新卡",
        "learning": "学习卡",
        "review": "复习卡",
    }.get(card_kind, card_kind)


def _response_strip() -> str:
    labels = ["重来", "困难", "良好", "简单"]
    options = "".join(
        f"<div class=\"response-option\">{escape(label)} ____</div>" for label in labels
    )
    return f"<div class=\"response-strip\">{options}</div>"


def _mathjax_ready_script() -> str:
    return """
(() => {
  const finish = () => pycmd("tomorrow-pdf-ready");
  const fail = (err) => pycmd("tomorrow-pdf-error:" + String(err));
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve()));

  const waitForMathJax = async () => {
    const startedAt = Date.now();
    while (true) {
      if (window.MathJax && MathJax.startup && MathJax.typesetPromise) {
        return;
      }
      if (Date.now() - startedAt > 15000) {
        throw new Error("MathJax failed to initialize");
      }
      await delay(50);
    }
  };

  const run = async () => {
    try {
      document.documentElement.classList.remove("night-mode");
      document.documentElement.setAttribute("data-bs-theme", "light");
      document.body.classList.remove("nightMode", "night_mode", "macos-dark-mode");
      await waitForMathJax();
      await MathJax.startup.promise;
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }
      await delay(500);
      MathJax.typesetClear();
      await MathJax.typesetPromise(Array.from(document.querySelectorAll(".print-card-body")));
      await nextFrame();
      await nextFrame();
      await delay(250);
      window.scrollTo(0, 0);
      finish();
    } catch (err) {
      fail(err);
    }
  };

  run();
})();
"""
