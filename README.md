# AI Extension

> A browser extension that acts as an AI-powered study assistant, answering questions from your personal Obsidian PDF vault using semantic search and Claude AI.

![Edge Extension](https://img.shields.io/badge/Microsoft%20Edge-Manifest%20V3-blue?logo=microsoftedge)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Claude](https://img.shields.io/badge/Powered%20by-Claude%20API-purple?logo=anthropic)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

AI Extension is a two-part system:

- **Browser Extension** — a floating overlay panel injected into any webpage in Microsoft Edge. Highlight text on any page and the assistant automatically picks it up as a question.
- **Python Companion Server** — a local Flask server that indexes your Obsidian PDF vault using sentence embeddings, retrieves relevant content via semantic search, and answers questions using the Claude API.

Your notes never leave your machine. The only external call is to the Claude API.

---

## Features

- **Floating overlay panel** — sits in the bottom-right corner of any webpage, minimises to a small circle when not needed
- **Highlight-to-ask** — select any text on a page and it's automatically sent to the assistant
- **Obsidian vault integration** — indexes all PDFs in your vault organised by topic folder
- **Semantic search** — finds the most relevant content across your notes using sentence embeddings (runs locally, no extra cost)
- **Source citations** — every answer includes the PDF filenames it drew from
- **Topic filtering** — select a subject from the dropdown to scope answers to that module
- **Server health indicator** — clear warning if the companion server isn't running

---

## Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐
│   Edge Extension    │◄──────►│  Python Companion Server │
│  (Floating Overlay) │  HTTP  │     localhost:5000        │
└─────────────────────┘        └────────────┬─────────────┘
                                            │
                               ┌────────────▼─────────────┐
                               │   OneDrive Obsidian Vault │
                               │   (PDFs by topic folder)  │
                               └────────────┬─────────────┘
                                            │
                               ┌────────────▼─────────────┐
                               │  ChromaDB Vector Index    │
                               │  sentence-transformers    │
                               └────────────┬─────────────┘
                                            │
                               ┌────────────▼─────────────┐
                               │       Claude API          │
                               │   claude-sonnet-4-6       │
                               └──────────────────────────┘
```

---

## Requirements

- Python 3.10+
- Microsoft Edge (Chromium)
- [Anthropic API key](https://console.anthropic.com)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Anzk0/Ai-Extension.git
cd Ai-Extension
```

### 2. Install Python dependencies

```bash
cd server
pip install -r requirements.txt
```

### 3. Configure the server

Copy the example config and fill in your details:

```bash
cp config.example.json config.json
```

Edit `config.json`:

```json
{
  "vault_path": "C:/Users/YourName/OneDrive/ObsidianVault",
  "claude_api_key": "sk-ant-...",
  "chroma_db_path": "./chroma_db"
}
```

> **Note:** `config.json` is gitignored — your API key will never be committed.

### 4. Organise your Obsidian vault

Each subfolder in your vault becomes a **topic** in the extension dropdown:

```
ObsidianVault/
├── Algorithms/
│   └── lecture1.pdf
├── Networks/
│   └── tcp-notes.pdf
└── Databases/
    └── week3.pdf
```

### 5. Start the companion server

```bash
cd server
python server.py
```

A system tray icon confirms the server is running. Console prints:
```
Study AI server running on http://localhost:5000
```

### 6. Load the extension in Edge

1. Open Edge → `edge://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** → select the `extension/` folder
4. The purple **AI** icon appears in your toolbar

---

## Usage

1. Navigate to any webpage
2. Click the **AI icon** in the toolbar to open the panel
3. Click **↺** to index your vault (first time only, or when you add new PDFs)
4. Select a **topic** from the dropdown
5. **Highlight any text** on the page — it auto-fills the input bar
6. Press **Enter** to get an answer with source citations

---

## Project Structure

```
Ai-Extension/
├── extension/
│   ├── manifest.json        # Manifest V3 extension config
│   ├── background.js        # Service worker — toolbar icon toggle
│   ├── content.js           # Injected into pages — overlay + highlight detection
│   ├── icons/               # Extension icons (16, 48, 128px)
│   └── overlay/
│       ├── overlay.html     # Floating panel markup
│       ├── overlay.css      # Dark theme styles
│       └── overlay.js       # Panel logic — chat, topics, API calls
└── server/
    ├── server.py            # Flask app — /status /topics /ask /index
    ├── indexer.py           # PDF reading, chunking, embeddings → ChromaDB
    ├── retriever.py         # Semantic search — ChromaDB query
    ├── claude_client.py     # Claude API integration
    ├── generate_icons.py    # One-time icon generation script
    ├── config.example.json  # Config template (copy to config.json)
    └── requirements.txt
```

---

## Running Tests

```bash
cd Ai-Extension
pytest -v
```

All 17 tests cover the server-side components (indexer, retriever, Claude client, endpoints).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Browser extension | HTML, CSS, JavaScript, Manifest V3 |
| AI model | Claude API — `claude-sonnet-4-6` |
| Companion server | Python, Flask |
| PDF reading | PyMuPDF |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector database | ChromaDB (local) |
| System tray | pystray |

---

## License

MIT
