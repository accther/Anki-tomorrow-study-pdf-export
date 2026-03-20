# Anki Tomorrow PDF Export

Anki add-on for macOS that exports tomorrow's study queue to a printable PDF.

This add-on is built for users who want to study on paper first and sync results back into Anki later. Instead of exporting an entire deck blindly, it simulates tomorrow's study day on a temporary collection snapshot and tries to preserve the order Anki would actually use.

## Features

- Choose one or more decks before exporting.
- Include child decks by default.
- Export tomorrow's due review and learning cards.
- Optionally include tomorrow's available new cards.
- Preserve Anki study order as closely as possible by reading the scheduler queue first.
- Split questions and answers for printing.
- Add writing space and a compact response strip under each question.
- Render through Anki WebView for better support of MathJax, LaTeX, and script-based templates.

## How It Works

1. The add-on reads your selected deck scope.
2. It creates a temporary SQLite snapshot of the current collection.
3. It shifts the snapshot forward to simulate tomorrow's study day.
4. It asks Anki's scheduler for the queued cards in order.
5. It renders the selected cards into HTML and prints that page to PDF.

This design keeps the live collection untouched during export.

## Project Files

- `__init__.py`: menu registration, deck picker dialog, export workflow.
- `scheduler_snapshot.py`: temporary collection snapshot, tomorrow simulation, queue extraction.
- `pdf_renderer.py`: HTML generation, WebView rendering, PDF output.
- `manifest.json`: package metadata for add-on distribution.
- `package_addon.sh`: creates the `.ankiaddon` package for AnkiWeb.
- `PUBLISHING.md`: release and publishing notes.
- `RELEASE_COPY.md`: bilingual release copy for GitHub and AnkiWeb.

## Install From Source

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Create a new add-on folder, for example `tomorrow_pdf_export`.
4. Copy these files into that folder:
   - `__init__.py`
   - `scheduler_snapshot.py`
   - `pdf_renderer.py`
   - `manifest.json`
5. Restart Anki.

## Package For AnkiWeb

Run:

```bash
chmod +x package_addon.sh
./package_addon.sh
```

Output:

```text
dist/tomorrow_pdf_export.ankiaddon
```

## Compatibility

- Platform: macOS
- Tested with: Anki 25.09.2

## Notes

- The export is based on the collection state at export time.
- If you keep studying or change deck options after exporting, tomorrow's in-app order may change accordingly.
- When the scheduler queue API is unavailable, the add-on falls back to a manual ordering strategy that may be less exact in advanced scheduling setups.
- Rendering of highly customized card templates can still depend on the template's own scripts and CSS.

## Documentation

- Chinese technical overview: `说明文档.zh-CN.md`
- Publishing guide: `PUBLISHING.md`
- Release copy: `RELEASE_COPY.md`
