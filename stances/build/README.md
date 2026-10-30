# Stance graphics generator

Rebuilds the 13 Tachikata stance cards (`stances/*.png`), the one-page `stance-reference-sheet.pdf`, and the printable guide PDF.

- `stance_data.py`: every stance (names, kanji, rank, foot positions and angles, weight split, key points, "Confirm with Sensei" flags) and the source URLs compared.
- `stance_render.py`: draws the SVG figure (side or front view), the top-down footprints on a 10 cm grid, and the weight bar.
- `build_stances.py`: `python3 stances/build/build_stances.py [cards|sheet|grid|all] [slug-filter]` (needs headless Chrome; cards are screenshots at 1204x864, the sheet is a Letter PDF; `grid` prints the HTML figure grid used in `index.html`).
- `build_guide_pdf.py`: rebuilds `shito-ryu-shodan-study-guide.pdf` from `index.html` (requirements, kata, kihon with the stance cards, study plan, written-test Q&A).

Run from the repo root. Foot plan coordinates are centimetres: +y forward, +x right, a foot is its heel centre plus an angle (clockwise positive).
The graphics are an unofficial study aid; your Sensei's instructions always come first.
