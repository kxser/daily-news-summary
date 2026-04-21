# daily-news-summary

Fetches headlines from two sources, feeds them to an LLM, and emails an HTML briefing every morning at 07:00.

## What it uses

- **NYT Top Stories API** — five categories (home, tech, science, national, politics)
- **NewsAPI** — US top headlines
- **OpenRouter + Gemini 3.1 Flash Lite** — the model that writes the briefing
- **Resend** — sends the email

## Flow

```
NYT API (×5) ─┐
              ├─► deduplicate ─► Gemini via OpenRouter ─► HTML email ─► Resend ─► inbox
NewsAPI ──────┘
```

Stateless — nothing is stored between runs.
