# Anki Tomorrow PDF Export

Anki add-on for macOS that exports tomorrow's study queue to a printable PDF.

## Features

- Choose the deck scope before exporting.
- Include child decks by default.
- Export tomorrow's due review / learning cards plus tomorrow's available new cards.
- Preserve the scheduler order by simulating tomorrow on a temporary collection snapshot.
- Produce an A4 PDF with prompt pages first and answer appendix at the end.

## Files

- `__init__.py`: menu registration, deck picker, export workflow.
- `scheduler_snapshot.py`: temporary collection copy, tomorrow simulation, queue extraction.
- `pdf_renderer.py`: HTML assembly and PDF rendering.

## Install

1. Open Anki.
2. Go to `Tools -> Add-ons -> View Files`.
3. Create a new add-on folder and place these files inside it.
4. Restart Anki.

## Notes

- The export is based on the collection state at export time.
- If you keep studying or change deck options after exporting, tomorrow's in-app order may change accordingly.
- The add-on uses a temporary copied collection and does not modify the live collection.
