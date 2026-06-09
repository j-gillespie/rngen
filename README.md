# rngen

ACME Product Release Notes Generator. A FastAPI backend and web UI that turns raw release details into structured Markdown release notes using the `Release Notes.docx` template.

## Features

- Select product, version, and release date from the web UI
- Paste raw engineering notes into the Details field
- Backend categorizes content into Overview, New Features, Resolved Issues, Known Issues, System Requirements & Compatibility, Installation, and Technical Support
- Displays generated release notes in Markdown with a live preview

## Project structure

```
app/
  main.py          # FastAPI server and API routes
  categorizer.py   # Sorts raw notes into template sections
  generator.py     # Builds Markdown from categorized content
static/
  index.html       # Web UI
templates/
  Release Notes.docx
run.py             # Local development entry point
requirements.txt
```

## Setup

```powershell
git clone https://github.com/j-gillespie/rngen.git
cd rngen
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:8000/ in your browser.

## API

`POST /api/generate`

```json
{
  "product": "Anvil",
  "version": "v2.1.0",
  "release_date": "2026-06-09",
  "details": "Raw release notes text..."
}
```

Response:

```json
{
  "markdown": "# Anvil v2.1.0 Release Notes\n..."
}
```

## Development workflow

1. Create a branch for your change
2. Make updates locally
3. Commit and push to GitHub
4. Open a pull request when ready

```powershell
git checkout -b feature/my-change
git add .
git commit -m "Describe your change"
git push -u origin feature/my-change
```
