# 🌾 AgriAdvisor AI — Project Blueprint
### Forge Gen AI Buildathon | Theme 2 — Climate, Resource Infrastructure & Global Supply Resilience

> **✅ BUILD STATUS (Nov 1, 2026): IMPLEMENTED & VERIFIED LIVE**
> Working code lives in `agri-advisor-ai/` — Python 3.11 · FastAPI · LangGraph · Gemini · ChromaDB · Sarvam voice · Streamlit UI.
> Full documentation: [`agri-advisor-ai/README.md`](agri-advisor-ai/README.md).
> Verified end-to-end: planner → geocode → live weather/mandi/RAG → synthesis → Hindi translation → TTS.
> Build log and deviations from this blueprint: see §11.

---

## 👥 Team Overview

| Field | Detail |
|---|---|
| **Track** | Theme 2 — Climate, Resource Infrastructure & Global Supply Resilience |
| **Problem** | Multilingual Agritech & Resource Advisory Assistant |
| **Team Size** | 2 members |
| **Primary Stack** | Python · FastAPI · LangGraph · Gemini · ChromaDB |
| **Status** | ✅ Core built & live-verified · voice + UI functional |

---

## 1. 🎯 Problem Statement

### Target Issue & Context
Indian farmers — especially smallholders — make critical decisions on **what to plant, when to harvest, and where to sell**, often relying on outdated advice, word of mouth, or intermediaries. They lack:
- Access to **real-time weather forecasts** at a local level
- Visibility into **live mandi (market) prices** to avoid exploitation
- Knowledge of **soil health** and crop-specific advisory
- Communication in their **native regional language**

This leads to crop losses, poor income, and food insecurity at scale.

### Target Audience
- 🧑‍🌾 Small and marginal farmers across rural India
- 🌾 Agricultural extension workers and NGOs
- 🏛️ State agriculture departments

---

## 2. 🧠 Solution Description

### High-Level Overview
**AgriAdvisor AI** is a voice-first, multilingual conversational assistant that:
1. Accepts farmer queries in **text or regional voice** (Hindi, Telugu, Tamil, Marathi, etc.)
2. Autonomously pulls **live weather forecasts, mandi prices, and soil data**
3. Reasons over the data using an **agentic LLM pipeline**
4. Returns **plain-language, actionable crop advice** in the farmer's language — as text and voice

The system goes beyond a simple chatbot — it uses an **agentic loop** (LangGraph) where the AI plans which data to fetch, calls multiple real-time tools, synthesizes the results, and explains its reasoning.

---

## 3. 🗺️ Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                  FARMER INPUT LAYER                      │
│  Voice (regional language) ──or── Text query            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│             SPEECH-TO-TEXT (STT) MODULE                  │
│  • Sarvam /speech-to-text (saaras:v4) — 22 Indian languages     │
│  • Output: transcript in spoken language (auto language detect) │
│  Output: Normalized English/Hindi text query            │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           LANGUAGE & INTENT DETECTION                    │
│  • Detect input language (langdetect / LLM prompt)      │
│  • Classify intent:                                     │
│    - Weather query          → weather_tool              │
│    - Price / sell query     → mandi_tool                │
│    - Crop advice query      → rag_tool                  │
│    - Soil / planting query  → soil_tool + rag_tool      │
│    - General / compound     → multi-tool                │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            AGENTIC REASONING LAYER (LangGraph)           │
│                                                         │
│   [Planner Node]                                        │
│      └─ Decides which tools to call & in what order     │
│                                                         │
│   [Tool Execution Nodes] ── parallel where possible     │
│      ├── 🌦️ fetch_weather()                             │
│      ├── 💰 fetch_mandi_price()                         │
│      ├── 🌱 fetch_soil_info()                           │
│      └── 📚 rag_crop_advisory()                         │
│                                                         │
│   [Synthesizer Node]                                    │
│      └─ LLM reasons over all tool outputs               │
│         Generates plain-language advice + reasoning     │
│                                                         │
│   [Error Handler / Retry Node]                          │
│      └─ If any tool fails → retry or use fallback API   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│          MULTILINGUAL RESPONSE GENERATION                │
│  • Translate advice back to farmer's language (LLM)     │
│  • Format: structured text with key points              │
│  • Include "Why?" section — show data that drove advice │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           TEXT-TO-SPEECH (TTS) MODULE                    │
│  • Sarvam AI TTS — Indian language voice output         │
│  • Returns audio file + text both                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               FARMER OUTPUT LAYER                        │
│  🔊 Voice reply in regional language                    │
│  📝 Text advice with bullet points                      │
│  📊 Data sources shown (weather, price, soil)           │
│  🗓️ Planting/harvesting schedule if applicable          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 🔧 Tool Details (What Each Tool Does)

### 🌦️ Tool 1 — `fetch_weather()`
| Field | Detail |
|---|---|
| **Purpose** | Fetch 7-day weather forecast for farmer's location |
| **Input** | District name or lat/long coordinates |
| **API** | Open-Meteo (free, no key) + IMD fallback |
| **Output** | Temperature, rainfall, humidity, wind — daily breakdown |
| **Use Case** | "Will it rain this week? Is it safe to spray pesticide?" |

### 💰 Tool 2 — `fetch_mandi_price()`
| Field | Detail |
|---|---|
| **Purpose** | Fetch today's live market prices for a crop |
| **Input** | Crop name + state/district |
| **API** | data.gov.in Agmarknet API (open, free) |
| **Output** | Min, Max, Modal price in ₹/quintal for nearby mandis |
| **Use Case** | "What is the price of tomato in Kurnool mandi today?" |

### 🌱 Tool 3 — `fetch_soil_info()`
| Field | Detail |
|---|---|
| **Purpose** | Fetch soil properties for a geographic location |
| **Input** | Lat/long coordinates |
| **API** | SoilGrids REST API (ISRIC — free, global) |
| **Output** | Soil pH, nitrogen, carbon, texture at depth levels |
| **Use Case** | "What crops are best for my soil?" |

### 📚 Tool 4 — `rag_crop_advisory()`
| Field | Detail |
|---|---|
| **Purpose** | Retrieve expert crop advice from a knowledge base |
| **Input** | Crop name + query (e.g., "pest control for rice") |
| **Knowledge Base** | ICAR crop guidelines + Kisan portal PDFs |
| **Tech** | ChromaDB vector store + embedding model |
| **Output** | Top-3 relevant advisory passages |
| **Use Case** | "How do I protect my wheat from rust disease?" |

---

## 5. 🏗️ Technical Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                         │
│                  Streamlit Web Application                    │
│   ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│   │ Voice Input  │  │ Text Input  │  │ Location Picker  │   │
│   │ (mic button) │  │ (chat box)  │  │ (district/pin)   │   │
│   └──────┬───────┘  └──────┬──────┘  └────────┬─────────┘   │
└──────────┼────────────────┼─────────────────┼──────────────┘
           │                │                 │
           ▼                ▼                 ▼
┌──────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER (FastAPI)                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              STT Module (Sarvam saaras:v4)             │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │        Language Detection + Intent Classifier          │  │
│  │               (LLM prompt-based)                      │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │           LangGraph Agentic Pipeline                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │ Weather  │ │  Mandi   │ │   Soil   │ │   RAG    │  │  │
│  │  │  Tool   │ │  Tool    │ │   Tool   │ │  Tool    │  │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │  │
│  │       └────────────┴────────────┴────────────┘         │  │
│  │                          │                             │  │
│  │              ┌───────────▼──────────┐                  │  │
│  │              │  LLM Synthesizer     │                  │  │
│  │              │  (Gemini 3.8 Flash)   │                  │  │
│  │              └───────────┬──────────┘                  │  │
│  └──────────────────────────┼──────────────────────────── ┘  │
│                             │                                 │
│  ┌──────────────────────────▼───────────────────────────┐    │
│  │            TTS Module (Sarvam bulbul:v3)               │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│                     DATA / EXTERNAL APIS                      │
│                                                              │
│  Open-Meteo    Agmarknet API    SoilGrids    ChromaDB        │
│  (Weather)     (Mandi Prices)   (Soil Data)  (Vector Store)  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 📦 Tech Stack & Requirements

### Core AI / Agent Framework
| Component | Tool | Why |
|---|---|---|
| LLM | **Gemini `gemini-3.8-flash`** (Google AI Studio) | Free tier, multilingual, structured-output planner *(updated: 1.5-flash is deprecated)* |
| Agent Framework | **LangGraph** | Stateful agentic loops, tool calling, error recovery |
| Embeddings | ChromaDB default local all-MiniLM (ONNX) | No key, offline, consistent vectors *(deviation: Google `text-embedding-004` needs the legacy SDK and would mismatch an existing store)* |
| Vector Store | **ChromaDB** (persistent local) | Zero setup, seeded on first request |

### Voice / Language
| Component | Tool | Why |
|---|---|---|
| STT (Speech-to-Text) | **Sarvam `saaras:v4`** (`POST /speech-to-text`) | 22 Indian languages, auto-detect *(updated: saarika deprecated)* |
| TTS (Text-to-Speech) | **Sarvam `bulbul:v3`** | Natural Indian language voice *(updated: bulbul:v2 deprecated)* |
| Language Detection | `langdetect` + declared-language override | Simple, reliable |
| Translation | Gemini in-prompt (translate node) | No extra API needed |

### Real-Time Data APIs
| Data | API | Cost | Key Required |
|---|---|---|---|
| Weather forecast | **Open-Meteo** | Free | ❌ No |
| Mandi prices | **data.gov.in Agmarknet** | Free | ✅ Yes (instant) |
| Soil properties | **SoilGrids (ISRIC)** | Free | ❌ No |
| Geolocation | **Nominatim (OpenStreetMap)** | Free | ❌ No |

### Frontend & Deployment
| Component | Tool | Why |
|---|---|---|
| UI | **Streamlit** | Fastest to build, easy to demo |
| Backend | **FastAPI** | Lightweight, async-ready |
| Deployment | **Hugging Face Spaces** | Free, supports Streamlit |
| Containerization | Docker (optional) | Clean deployment |

### Python Libraries
| Library | Purpose |
|---|---|
| `langgraph` | Agentic pipeline |
| `langchain` | LLM wrappers, tool definitions |
| `chromadb` | Vector store |
| `streamlit` | UI |
| `fastapi` | API server |
| `httpx` / `requests` | External API calls |
| `sarvam-client` | STT + TTS |
| `langdetect` | Language detection |
| `pydantic` | Data validation |
| `python-dotenv` | Environment variable management |

---

## 7. 📁 Actual Project Structure (as built)

```
agri-advisor-ai/
│
├── README.md                    # Full setup + architecture + verification status
├── requirements.txt             # All Python dependencies
├── .env.example                 # API keys template (.env holds real keys)
├── pytest.ini
│
├── app/
│   ├── main.py                  # FastAPI entrypoint: /ask /transcribe /tts /health /kb/stats
│   ├── streamlit_app.py         # Streamlit chat UI (voice upload, reasoning trace)
│   │
│   ├── agent/
│   │   ├── state.py             # TypedDict agent state + tool-output reducer
│   │   ├── llm.py               # Gemini factory + structured Plan schema
│   │   ├── nodes.py             # planner / tools / synthesizer / error handler
│   │   ├── graph.py             # LangGraph wiring + translate node
│   │   └── service.py           # public answer_query() entrypoint
│   │
│   ├── tools/
│   │   ├── schemas.py           # pydantic models (WeatherReport, MandiPrice…)
│   │   ├── weather_tool.py      # Open-Meteo 7-day integration
│   │   ├── mandi_tool.py        # Agmarknet JSON/XML parser + live local filter
│   │   ├── soil_tool.py         # SoilGrids integration
│   │   └── rag_tool.py          # ChromaDB ingest + retrieval
│   │
│   ├── voice/
│   │   ├── stt.py               # Sarvam saaras:v4 speech-to-text
│   │   └── tts.py               # Sarvam bulbul:v3 text-to-speech (WAV)
│   │
│   ├── knowledge_base/
│   │   ├── docs/seed_advisory.md  # crop advisory corpus (rice/wheat/tomato…)
│   │   └── chroma_store/          # (auto-created) vector DB
│   │
│   └── utils/
│       ├── config.py            # env vars + API endpoints
│       ├── geo.py               # geocoding with provider fallback
│       └── language.py          # langdetect language identification
│
└── tests/
    └── test_tools.py            # live-API tests (geocode, weather, soil, RAG)
```

---

## 8. 🔑 API Keys Needed

| API | Where to Get | Time |
|---|---|---|
| **Google AI Studio** (Gemini) | [aistudio.google.com](https://aistudio.google.com) | 2 min |
| **Sarvam AI** (Voice) | [sarvam.ai](https://sarvam.ai) | 5 min |
| **data.gov.in** (Agmarknet) | [data.gov.in](https://data.gov.in) | 10 min |

> Open-Meteo, SoilGrids, and Nominatim are **fully free with no API key**.

---

## 9. 🏆 Judging Alignment

| Pillar | How We Score |
|---|---|
| **Technical Architecture (20 pts)** | LangGraph agentic pipeline, 4 real-time tools, RAG, modular codebase |
| **AI Reasoning & Agentic Execution (25 pts)** | Multi-step tool planning, error recovery/retry, source attribution in output |
| **Problem Relevance & USP (25 pts)** | 140M+ farmer audience, voice-first regional language, no existing free tool does this end-to-end |
| **Live Demo & Robustness (30 pts)** | All real APIs, graceful API failure fallback, runs on Streamlit Cloud |

### Our USP Statement
> *"Unlike generic chatbots, AgriAdvisor autonomously pulls live IMD weather, Agmarknet mandi prices, and SoilGrids soil data — reasons over them with a stateful agentic loop — and delivers hyper-local crop advice in the farmer's native language, voice-first."*

---

## 10. 🗓️ Build Timeline — PROGRESS

```
Day 1 — Foundation ✅ DONE
  ├── Set up project structure & environment ✅
  ├── Get all API keys working (Google / Sarvam / data.gov.in) ✅
  ├── Build & test each tool independently ✅ (weather live-tested, mandi live-tested,
  │     soil coded but SoilGrids currently in a global outage — retries built in)
  └── Set up ChromaDB + ingest crop advisory docs ✅ (seed_advisory.md → 20+ vectors)

Day 2 — Core Agent ✅ DONE
  ├── Build LangGraph pipeline (planner + tools + synthesizer + error handler) ✅
  ├── Test multi-tool reasoning end-to-end ✅ (compound Q → mandi + weather, live)
  ├── Add error handling & retry logic ✅ (retries ×2, graceful degradation verified)
  └── Build multilingual response formatting ✅ (Hindi answer verified live)

Day 3 — Voice + UI ✅ DONE
  ├── Integrate Sarvam STT (saaras:v4) + TTS (bulbul:v3) ✅ both live-verified
  ├── Build Streamlit UI (voice input, text input, location picker, trace expander) ✅
  ├── Connect frontend to FastAPI backend ✅
  └── End-to-end testing with realistic farmer queries ✅

Day 4 — Polish & Deploy 🔄 REMAINING
  ├── Deploy (Streamlit Cloud / Hugging Face Spaces / Render)
  ├── Record demo video (2–3 min)
  ├── Architecture diagram image for README
  └── Prepare pitch deck (5–7 slides)
```

---

## 11. 📋 Build Log — What Was Done & Fixed

### Delivered
| Piece | Where | Verified |
|---|---|---|
| FastAPI backend (`/ask`, `/transcribe`, `/tts`, `/health`, `/kb/stats`) | `app/main.py` | ✅ boots, `/health` OK |
| LangGraph agent: planner → parallel tools → synthesizer → error handler → translate | `app/agent/` | ✅ full runs live |
| Live tools: geocode, weather, mandi, soil, RAG | `app/tools/` | ✅ (soil pending provider recovery) |
| Voice STT/TTS | `app/voice/` | ✅ Hindi TTS WAV + STT endpoint |
| Streamlit chat UI with reasoning-trace expander | `app/streamlit_app.py` | — |
| Test suite (live-API integration tests) | `tests/test_tools.py` | ✅ 4/4 passing |

### Fixes applied during verification
1. **Gemini model deprecations** — `gemini-1.5-flash` → `gemini-2.0-flash` → **`gemini-3.8-flash`** (404s resolved).
2. **Gemini content format** — new API returns content as typed blocks; added `_extract_text()` normalizer so answers render as text, not raw dicts.
3. **data.gov.in returned XML** — added dual JSON/XML parser (`_parse_payload`) for Agmarknet.
4. **Agmarknet ignores field filters** — fetches the live national feed and filters locally by commodity/district/state; widens to nationwide when the district has no rows (still real-time data — zero hardcoding).
5. **Sarvam STT endpoint 404** — migrated `/speech-to-text/translate` → **`/speech-to-text`** with `saaras:v4` + BCP-47 `language_code`.
6. **Sarvam TTS deprecation** — `bulbul:v2` → **`bulbul:v3`**.
7. **Async httpx misuse** — `async with client, client.get(...)` fixed to proper `await client.get(...)` across all tools.
8. **RAG sync tool awaited blindly** — fixed coroutine/sync detection in `_execute`.
9. **LLM-down resilience** — synthesizer no longer crashes the graph; it routes to the error handler, which emits a data-grounded fallback from whichever tools succeeded (verified without API keys).

### Second review round — priority fixes (Nov 1)
| # | Issue | Fix | Verified |
|---|---|---|---|
| H1 | Mandi pulled 2000 records per query (~5-10s) | **30-min in-memory feed cache** (`_get_feed()`); also truncates results to `limit` rows | ✅ first fetch 5.36s → cached 0.0000s |
| H2 | Synthesizer called prompt+LLM as two thread hops | single **chained `prompt \| llm` invoke** in one `to_thread` | ✅ |
| H3 | Conditional edge rerouted successful synthesis when `attempts > 0` | route on **`answer_en` presence only** | ✅ |
| H4 | Only one RAG doc | **5 crop-tagged docs** (rice, wheat, tomato, paddy-water + seed) → 15 vectors, crop filter works | ✅ ingested 10 new vectors |
| H5 | No location validation in UI | sidebar help text + non-blocking blank hint + **friendly warning when geocode fails** ("try Kurnool/Indore") | ✅ |
| M1 | Incomplete `strip_emoji()` | full emoji-block regex (U+1F000–1FAFF, symbols, dingbats) + markdown noise removal | ✅ |
| M2 | No conversation memory | `history` field on `/ask` — **last 3 turns fed to planner & synthesizer** ("What about next week?" follow-up verified) | ✅ |
| M3 | Hardcoded `AGRI_API_URL` undocumented | `.env.example` now documents local vs deployed values | ✅ |
| M4 | Runtime logs in repo | `uvicorn.log` / `uvicorn.err` deleted (already in `.gitignore`) | ✅ |
| M5 | Confusing empty `agri-advisor/` folder | removed — root is `AgriAdvisor_Blueprint.md` + `agri-advisor-ai/` only | ✅ |
| L1 | No live progress in UI | **`POST /ask/stream`** (NDJSON) + Streamlit `st.status` renders plan → tool → synthesis trace in real time | ✅ streamed end-to-end |
| L2 | Reasoning trace not shown | already rendered in "🧠 Agent reasoning trace" expander | ✅ |
| L3 | Quick prompts need Enter | buttons auto-submit in the same run (`pending` pop) | ✅ |
| L4 | No architecture diagram | `docs/architecture.md` — mermaid system diagram + data-source table (linked from README) | ✅ |
| L5 | README key setup | Getting Started section with all 3 keys + `AGRI_API_URL` | ✅ |
| — | RAG embedding dependency | switched Chroma to **local ONNX embeddings** (Google EF needs legacy SDK; mixing models would corrupt retrieval) | ✅ 15 vectors retrievable |

### Known external issues (handled, not code bugs)
- **SoilGrids (ISRIC)** currently 503s globally → retries ×2, answer flags "unavailable", recovers automatically when the provider is back.
- **Slow LLM synthesis** (~1–2 min for long mandi payloads) — acceptable for demo; a future optimization is truncating the price list before the prompt.

### Remaining for submission
- [ ] Live deployment URL (Streamlit Cloud / HF Spaces) — set `AGRI_API_URL` when deploying
- [ ] Demo video (2–3 min, end-to-end) — use `/ask/stream` for the live-trace visual
- [ ] GitHub repo push (README, `docs/architecture.md` diagram)
- [ ] Pitch deck (5–7 slides)
- [x] Expand knowledge base: 5 crop docs ingested (rice, wheat, tomato, paddy, seed)
- [ ] Optional: re-test soil tool once ISRIC is back

---

*Blueprint prepared for Forge Gen AI Buildathon — November 2026 (updated with build status Nov 1, 2026)*
