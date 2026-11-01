# 🌾 AgriAdvisor AI

**Forge Gen AI Buildathon · Theme 2 — Climate, Resource Infrastructure & Global Supply Resilience**
*Multilingual Agritech & Resource Advisory Assistant — voice-first, real-time, agentic.*

> A LangGraph agentic pipeline that plans which live data to fetch (weather · mandi prices · soil · expert advisories), runs the tools in parallel with retries, reasons over the results with Gemini, and answers the farmer in their own language — as text **and** voice.

---

## 1. The Problem

Indian smallholder farmers decide **what to plant, when to spray, and where to sell** without:

- 🌦️ localized, current **weather forecasts**
- 💰 visibility into **live mandi prices** (often exploited by intermediaries)
- 🌱 knowledge of **soil health** for crop/fertilizer decisions
- 🗣️ advice in their **native regional language**

Outcome: crop loss, spoiled harvests, and income left on the table — affecting 140M+ farming households.

**Target users:** small/marginal farmers · extension workers & NGOs · state agriculture departments.

---

## 2. The Solution

**AgriAdvisor AI** answers a farmer's question end-to-end:

```
Voice/Text query (any Indian language)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  LANGGRAPH AGENT LOOP                                       │
│                                                             │
│  ① Planner (Gemini + keyword heuristics)                    │
│      └─ picks tools: geocode · weather · mandi · soil · rag │
│  ② Tool execution (parallel, retry ×2, degrade gracefully)  │
│      ├─ 📍 geocode        Open-Meteo geocoding / Nominatim  │
│      ├─ 🌦️ weather        Open-Meteo 7-day forecast         │
│      ├─ 💰 mandi          Agmarknet live prices (data.gov.in│)
│      ├─ 🌱 soil           SoilGrids (ISRIC) pH / N / texture│
│      └─ 📚 rag            ChromaDB crop-advisory retrieval  │
│  ③ Synthesizer (Gemini)                                     │
│      └─ grounded advice + "Why?" section citing tool data   │
│  ④ Error handler                                            │
│      └─ if LLM unavailable → verified raw data fallback     │
│  ⑤ Translator                                               │
│      └─ renders answer in farmer's language                 │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
Answer: text + optional voice (Sarvam bulbul:v3 TTS) + sources + reasoning trace
```

**Why it's not just a chatbot:** every number in the answer comes from a live API
called during that request; the reasoning trace is shown to the user; failed tools are
retried and the answer explicitly flags what couldn't be fetched. Nothing is hardcoded.

---

## 3. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | **Python 3.11 · FastAPI** | async endpoints, `/docs` OpenAPI UI |
| Agent loop | **LangGraph** state graph | planner → tools → synthesizer → error_handler → translate |
| LLM | **Gemini `gemini-3.8-flash`** | via `langchain-google-genai`; structured-output planner |
| RAG | **ChromaDB** + local all-MiniLM ONNX embeddings | local persistent store, seeded from `app/knowledge_base/docs/` (no key, offline-capable) |
| Live weather | Open-Meteo API | no key, 7-day forecast |
| Live prices | Agmarknet — data.gov.in | free API key, dual JSON/XML parser, **30-min feed cache** |
| Soil data | SoilGrids (ISRIC) | no key |
| Geocoding | Open-Meteo geocoding → Nominatim fallback | district → lat/long |
| Voice | **Sarvam AI** — STT `saaras:v4`, TTS `bulbul:v3` | 14 Indian languages |
| UI | **React (Vite)** chat app | streaming agent trace, mic voice input, TTS playback, responsive |
| Tests | pytest (live-API integration tests) | |

---

## 4. Project Structure

```
NXT_Wave/                          ← repository root (you are here)
├── README.md
├── AgriAdvisor_Blueprint.md       ← buildathon blueprint
├── .gitignore
│
└── agri-advisor-ai/               ← run all commands from this folder
    ├── docs/architecture.md       ← system diagram (mermaid) + data-source table
    ├── requirements.txt
    ├── .env.example               ← copy to .env, add your keys
    ├── pytest.ini
    │
    ├── app/
    │   ├── main.py                # FastAPI: /ask /transcribe /tts /health /kb/stats + serves frontend
    │   │
    │   ├── agent/
    │   │   ├── state.py           # TypedDict agent state + tool-output reducer
    │   │   ├── llm.py             # Gemini factory + structured Plan schema
    │   │   ├── nodes.py           # planner, tools, synthesizer, error handler
    │   │   ├── graph.py           # LangGraph wiring + translate node
    │   │   └── service.py         # public answer_query() entrypoint
    │   │
    │   ├── tools/
    │   │   ├── schemas.py         # pydantic models (WeatherReport, MandiPrice…)
    │   │   ├── weather_tool.py    # Open-Meteo 7-day forecast
    │   │   ├── mandi_tool.py      # Agmarknet live feed + JSON/XML parser + local filter
    │   │   ├── soil_tool.py       # SoilGrids pH/N/OC/texture
    │   │   └── rag_tool.py        # ChromaDB ingest + retrieval
    │   │
    │   ├── voice/
    │   │   ├── stt.py             # Sarvam saaras:v4 speech-to-text
    │   │   └── tts.py             # Sarvam bulbul:v3 text-to-speech (WAV)
    │   │
    │   ├── knowledge_base/
    │   │   ├── docs/                   # crop advisory corpus, one doc per crop:
    │   │   │   ├── seed_advisory.md        # groundnut, onion, cotton
    │   │   │   ├── rice_pest_disease.md    # BPH, blast, borers
    │   │   │   ├── wheat_agronomy.md       # sowing, rusts, irrigation
    │   │   │   ├── tomato_cultivation.md   # blights, drip, market timing
    │   │   │   └── paddy_water_management.md  # AWD, drainage, nutrients
    │   │   └── chroma_store/          # (auto-created) vector DB
    │   │
    │   └── utils/
    │       ├── config.py          # env vars + API endpoints
    │       ├── geo.py             # geocoding with fallback chain
    │       └── language.py        # langdetect language identification
    │
    ├── frontend/                  # React (Vite) chat UI
    │   ├── package.json           # npm scripts: dev / build / preview
    │   ├── vite.config.js         # dev proxy → localhost:8000
    │   ├── src/
    │   │   ├── App.jsx            # chat state, streaming, TTS orchestration
    │   │   ├── api.js             # /ask/stream NDJSON reader + /transcribe + /tts
    │   │   ├── styles.css         # responsive agri-themed design
    │   │   └── components/        # Sidebar, ChatMessage, ChatInput, TracePanel, Markdown
    │   └── dist/                  # (built) served by FastAPI at "/"
    │
    └── tests/
        └── test_tools.py          # live tests: geocode, weather, soil, RAG, lang
```

---

## 5. API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/ask` | Main advisory: `{query, location_hint, declared_lang?, crop_hint?, history?}` → plan + live data + grounded answer + reasoning trace |
| `POST` | `/ask/stream` | Same as `/ask`, but NDJSON stream: `{"type":"trace"}` events as the agent works, then `{"type":"done"}` (powers the live progress UI) |
| `POST` | `/transcribe?lang_hint=hi` | multipart audio → transcript (Saaras v4) |
| `POST` | `/tts` | `{text, lang_code}` → WAV bytes |
| `GET` | `/health` | status + configured-keys check |
| `GET` | `/kb/stats` | vector count in the RAG store |

Interactive docs: **http://localhost:8000/docs**

---

## 6. Getting Started

```bash
# 0. enter the project folder
cd agri-advisor-ai

# 1. install
pip install -r requirements.txt

# 2. keys  (Windows: copy, Linux/macOS: cp)
copy .env.example .env
#    GOOGLE_API_KEY   → aistudio.google.com      (Gemini)
#    DATA_GOV_API_KEY → data.gov.in              (Agmarknet)
#    SARVAM_API_KEY   → sarvam.ai                (voice)

# 3. backend + UI → http://localhost:8000
uvicorn app.main:app --reload
#    FastAPI also serves the built React UI from frontend/dist at "/"

# 4. (optional) React dev server with hot reload → http://localhost:5173
cd frontend
npm install
npm run dev          # proxies API calls to localhost:8000

#    rebuild the production UI (served by FastAPI at "/"):
npm run build
```

> The RAG knowledge base auto-ingests `app/knowledge_base/docs/*.md` on first request
> (`GET /kb/stats` to confirm the vector count).

### Example request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I sell my tomato now? What is the price?", "location_hint": "Kurnool"}'
```

---

## 7. Verified Working (as of build)

| Component | Status |
|---|---|
| Planner — heuristic + LLM structured output | ✅ verified live |
| Geocoding (dual provider) | ✅ verified live |
| Weather — Open-Meteo 7-day | ✅ verified live |
| Mandi — Agmarknet live prices | ✅ verified live (54 tomato rows fetched today) |
| RAG retrieval from ChromaDB | ✅ verified live |
| Synthesis with "Why?" attribution | ✅ verified live |
| Hindi translation of grounded answer | ✅ verified live |
| Voice TTS (Hindi → WAV) | ✅ verified live |
| Voice STT endpoint | ✅ verified live (auto language detect) |
| Graceful degradation (LLM/tool down → raw-data fallback) | ✅ verified live |
| React UI — built & served at `/` by FastAPI | ✅ verified live (index, assets, health) |
| `/ask/stream` NDJSON → React live trace | ✅ verified live (trace + done events) |
| Test suite | ✅ 4/4 passing (soil test skipped — SoilGrids 503) |

**Known external issues handled:**
- **SoilGrids** intermittently 503s → tool retries ×2 and the answer flags it; service recovers automatically.
- **data.gov.in** returns XML sometimes and doesn't support field filters → dual JSON/XML parser + local filtering over the live feed (still real-time data, nothing hardcoded).

---

## 8. Resilience / Robustness Design (judging pillar 4)

- Every tool wrapped in try/except with **2 retries + backoff** — a dead API never crashes the request.
- Missing geolocation → weather/soil are dropped from the plan; mandi/rag still run.
- LLM unavailable → **error handler** emits a data-grounded fallback built from whichever tools *did* succeed.
- TTS/STT failures return clean JSON errors; the chat UI continues text-only.
- **Conversation memory** — the last 3 Q&A turns are passed to the planner and
  synthesizer, so follow-ups like *"What about next week?"* resolve correctly.
- **Mandi feed cache (30 min)** — the 2000-row national feed is fetched once and
  reused across requests, keeping repeated price queries near-instant.
- **Live agent trace** — `/ask/stream` emits NDJSON events while the agent runs; the
  React UI renders them inside a live trace panel so judges watch the plan → tool →
  synthesis sequence happen in real time.
- All responses carry `sources` and a `reasoning_trace` (visible in the UI's "🧠 Agent reasoning trace" expander) for source attribution.

---

## 9. Tests

```bash
pytest tests -v            # live-API tests (needs network)
pytest -k "not soil"       # skip if SoilGrids is having an outage
```

Covers: commodity aliasing, language detection, live geocode fallback,
live 7-day weather, SoilGrids retrieval.

---

## 10. Zero-Tolerance Compliance ✅

*No hardcoded datasets, no mock JSON, no static numbers.* Every response is assembled
from Open-Meteo, Agmarknet (data.gov.in), SoilGrids, ChromaDB-retrieved advisories,
and Gemini reasoning executed **during the request**.

---

*Forge Gen AI Buildathon — Theme 2. Prepared November 2026.*
