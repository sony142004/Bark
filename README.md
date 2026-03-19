# 🤖 Bark.com AI Lead Agent

> **3-Part Automation System** — Scrape → Score → Pitch

---

## How It Works

```
main.py
  │
  ├── Part 1 ── scraper.py         Login + extract leads from Bark
  ├── Part 2 ── ai_brain.py        Score each lead 0.0 → 1.0 (GPT-4o)
  └── Part 3 ── pitch_generator.py If score > 0.8 → write a personalized pitch
```

---

## Part 1 — Scraper (`scraper.py`)
- Logs into `bark.com` with human-like typing and delays
- Navigates to **Buyer Requests / Dashboard**
- Slowly scrolls to trigger dynamic content
- Extracts: **Title, Description, Budget, Location**
- Falls back to realistic mock data if login is unavailable

## Part 2 — AI Brain (`ai_brain.py`)
- Sends each lead to **GPT-4o** with a clear ICP prompt
- Returns a **JSON score** (`0.0` = no match → `1.0` = perfect)
- Includes a short **reasoning** string explaining the score
- Threshold: `score ≥ 0.8` → worth pursuing

## Part 3 — Pitch Generator (`pitch_generator.py`)
- Activated **only for leads scoring above 0.8**
- Writes a **personalized 3-paragraph proposal**
- Must reference **≥ 2 specific details** from the buyer's own description
- Ends with a call-to-action

---

## Project Structure

```
BarkAgent/
├── main.py              ← Run this  (orchestrates all 3 parts)
├── scraper.py           ← Part 1: Browser automation
├── ai_brain.py          ← Part 2: LLM scoring
├── pitch_generator.py   ← Part 3: Pitch generation
├── requirements.txt     ← Dependencies
├── .env.example         ← API key template
└── videos/              ← Auto-generated session recordings
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install

# 2. Configure credentials
copy .env.example .env
# Then edit .env with your keys

# 3. Run the agent
python main.py
```

**`.env` file:**
```
OPENAI_API_KEY=sk-proj-...
BARK_EMAIL=your@email.com
BARK_PASSWORD=yourpassword
```

> **Note:** If no Bark credentials are provided, the agent demonstrates the full
> AI pipeline using realistic mock leads — you still see scoring and pitch generation working.

---

## Tech Stack
| Tool | Purpose |
|---|---|
| `Playwright` | Browser automation (Part 1) |
| `OpenAI GPT-4o` | Lead scoring + pitch writing (Parts 2 & 3) |
| `Rich` | Coloured terminal output |
| `python-dotenv` | Secure credential management |
