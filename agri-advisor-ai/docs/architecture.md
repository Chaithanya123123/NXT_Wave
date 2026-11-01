# AgriAdvisor AI — System Architecture

```mermaid
flowchart TD
    U["🧑‍🌾 Farmer — text or regional voice<br/>(Streamlit UI)"] -->|"POST /ask/stream"| API

    subgraph API["FastAPI backend — app/main.py"]
        API["/ask · /ask/stream · /transcribe · /tts"]
    end

    API --> P

    subgraph AGENT["LangGraph agent loop — app/agent/"]
        P["① Planner<br/>Gemini structured output + keyword heuristics<br/>(with conversation history)"]
        P --> G{"📍 Geocode needed?"}
        G -->|yes| GEO["geocode node<br/>Open-Meteo → Nominatim fallback"]
        GEO --> T
        G -->|no| T
        T["② Tool fan-out (parallel, retry ×2)"]
        T --> W["🌦️ Weather<br/>Open-Meteo 7-day"]
        T --> M["💰 Mandi<br/>Agmarknet live feed<br/>(30-min cache)"]
        T --> S["🌱 Soil<br/>SoilGrids"]
        T --> R["📚 RAG<br/>ChromaDB advisories"]
        W & M & S & R --> SYN["③ Synthesizer<br/>Gemini — grounded advice + Why?"]
        SYN -->|answer missing| EH["④ Error handler<br/>verified raw-data fallback"]
        EH --> TR
        SYN -->|answer ok| TR["⑤ Translator<br/>Gemini → farmer's language"]
    end

    TR -->|NDJSON trace events| API
    API --> UI["Streamlit st.status — live agent trace<br/>+ answer + reasoning-trace expander"]
    UI -.optional.-> TTS["🔊 Sarvam bulbul:v3 → WAV"]

    V["🎤 Voice input"] -.-> STT["Sarvam saaras:v4 STT"]
    STT --> API

    classDef live fill:#e8f5e9,stroke:#2e7d32
    classDef ai fill:#e3f2fd,stroke:#1565c0
    class W,M,S live
    class P,SYN,TR ai
```

## Data sources (all fetched live at request time — no hardcoded datasets)

| Source | Used for | Key needed |
|---|---|---|
| Open-Meteo (forecast + geocoding) | 7-day weather, district → lat/long | ❌ |
| Nominatim (OpenStreetMap) | geocode fallback | ❌ |
| Agmarknet / data.gov.in | live mandi prices (national feed, 30-min cache) | ✅ |
| SoilGrids (ISRIC) | soil pH / nitrogen / texture | ❌ |
| ChromaDB local store | crop advisory passages (RAG) | ❌ |
| Google Gemini (`gemini-3.8-flash`) | planner, synthesis, translation | ✅ |
| Sarvam AI (`saaras:v4` STT, `bulbul:v3` TTS) | voice in/out | ✅ |
