"""Agentic pipeline nodes — planner, tool execution, synthesizer, error handling."""

import asyncio
import datetime as _dt

from pydantic import BaseModel, Field

from app.tools.mandi_tool import fetch_mandi_prices
from app.tools.rag_tool import rag_crop_advisory
from app.tools.soil_tool import fetch_soil
from app.tools.weather_tool import fetch_weather
from app.utils.geo import geocode

CODE_LABELS = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil",
    "mr": "Marathi", "kn": "Kannada", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi", "ml": "Malayalam",
}


def _format_history(history) -> str:
    """Render the last few Q&A turns for LLM context (follow-up questions)."""
    if not history:
        return "(none)"
    lines = []
    for turn in history[-6:]:
        role = turn.get("role", "?")
        text = str(turn.get("content", ""))[:220]
        lines.append(f"{role}: {text}")
    return "\n".join(lines)


def _extract_text(reply) -> str:
    """Newer Gemini wrappers return content as a list of typed blocks."""
    content = getattr(reply, "content", reply)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" or "text" in block:
                    parts.append(str(block.get("text", "")))
            elif hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts).strip()
    return str(content)


def _trace(state: dict, message: str) -> None:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%H:%M:%S")
    state.setdefault("reasoning_trace", []).append(f"[{stamp}] {message}")


async def _safe_geocode(state: dict) -> dict:
    hint = state.get("location_hint") or ""
    if not hint:
        return {"tool": "geocode", "ok": False, "data": {}, "error": "no location hint"}
    try:
        result = await geocode(hint)
        if not result:
            return {"tool": "geocode", "ok": False, "data": {}, "error": "no match found"}
        return {"tool": "geocode", "ok": True, "data": result.model_dump()}
    except Exception as exc:  # noqa: BLE001
        return {"tool": "geocode", "ok": False, "data": {}, "error": str(exc)}


# ------------------------------------------------------------ Planner

class _Plan(BaseModel):
    geocode: bool = False
    weather: bool = False
    mandi: bool = False
    soil: bool = False
    rag: bool = False
    crop: str = Field("", description="Crop name if inferable")


PLANNER_SYSTEM = """You are the planner of an agricultural advisory agent for Indian farmers.
Given the farmer's question, decide which live data tools must run:
- geocode: resolve district/village names to coordinates (needed before weather/soil).
- weather: 7-day local forecast (rain, temperature, humidity) — for rain/irrigation/heat decisions.
- mandi: live per-quintal market prices — for price, selling, market timing.
- soil: pH/nitrogen/texture data — for crop suitability or fertilizer questions.
- rag: expert agronomy passages — for pest, disease, sowing, harvest, technique questions.
Extract the crop name when mentioned. Respond with a _Plan object only."""


async def node_planner(state: dict) -> dict:
    q = (state.get("query") or "").lower()
    wants: set[str] = set()

    keyword_map = {
        "mandi": ["price", "mandi", "sell", "rate", "market", "quintal", "bhav", "बेच", "कीमत", "भाव", "ధర", "వేల"],
        "weather": ["rain", "weather", "spray", "irrigat", "temperature", "forecast", "heat", "बारिश", "मौसम", "వర్ష", "వాతావరణ"],
        "soil": ["soil", "nutrient", "fertilizer", "which crop", "suitable", "मिट्टी", "నేల", "ఎరువు"],
        "rag": ["pest", "disease", "sow", "harvest", "technique", "yield", "manure", "कीट", "बीमारी", "फसल", "పురుగ", "పండించు"],
    }
    for tool, words in keyword_map.items():
        if any(w in q for w in words):
            wants.add(tool)

    # LLM refinement — catches compound questions heuristics miss.
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from app.agent.llm import get_gemini

        prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM),
            ("human", "Location: {loc}\nRecent conversation:\n{history}\nQuestion: {q}"),
        ])
        chain = prompt | get_gemini().with_structured_output(_Plan)
        plan = await asyncio.to_thread(chain.invoke, {
            "loc": state.get("location_hint", "?"),
            "q": state["query"],
            "history": _format_history(state.get("history")),
        })
        for tool, ok in (("weather", plan.weather), ("mandi", plan.mandi), ("soil", plan.soil), ("rag", plan.rag), ("geocode", plan.geocode)):
            if ok:
                wants.add(tool)
        if plan.crop and not state.get("crop_hint"):
            state["crop_hint"] = plan.crop
    except Exception as exc:  # noqa: BLE001 — heuristics carry the plan if the LLM is down
        _trace(state, f"planner LLM unavailable ({type(exc).__name__}); using heuristics")

    if not wants and not q:
        wants.add("rag")

    needs_geo = (wants & {"weather", "soil"}) and state.get("latitude") is None
    planned = list(dict.fromkeys((["geocode"] if needs_geo else []) + sorted(wants)))
    state["plan"] = planned
    _trace(state, f"plan -> {planned}; crop={state.get('crop_hint') or 'n/a'}")
    return state


# ------------------------------------------------------------ Tool execution

TOOL_FUNCS = {
    "weather": lambda s: fetch_weather(s["latitude"], s["longitude"], s.get("location_name", ""), s.get("state_hint", "")),
    "mandi": lambda s: fetch_mandi_prices(s.get("crop_hint") or "Tomato", district=s.get("location_name", "")),
    "soil": lambda s: fetch_soil(s["latitude"], s["longitude"]),
    "rag": lambda s: rag_crop_advisory(s["query"], s.get("crop_hint", "")),
}


async def _execute(name: str, state: dict, retries: int = 2) -> dict:
    func = TOOL_FUNCS.get(name)
    if func is None:
        return {"tool": name, "ok": False, "data": {}, "error": f"unknown tool {name}"}
    for attempt in range(1, retries + 1):
        try:
            outcome = func(state)
            result = await outcome if asyncio.iscoroutine(outcome) else outcome
            data = result if not hasattr(result, "model_dump") else result.model_dump()
            _trace(state, f"{name} ok (attempt {attempt})")
            return {"tool": name, "ok": True, "data": data, "error": None}
        except Exception as exc:  # noqa: BLE001
            err = str(exc)[:300]
            _trace(state, f"{name} failed attempt {attempt}: {err}")
            if attempt == retries:
                return {"tool": name, "ok": False, "data": {}, "error": err}
            await asyncio.sleep(1.0)
    return {"tool": name, "ok": False, "data": {}, "error": "exhausted retries"}


async def node_execute_tools(state: dict) -> dict:
    outputs: dict = state.get("tool_outputs") or {}

    if "geocode" in state["plan"]:
        geo = await _safe_geocode(state)
        outputs["geocode"] = geo
        if geo["ok"]:
            state["location_name"] = geo["data"].get("name")
            state["latitude"] = geo["data"].get("latitude")
            state["longitude"] = geo["data"].get("longitude")
            state["state_hint"] = geo["data"].get("state", "")
            _trace(state, f"geocode ok -> {state['location_name']} ({state['latitude']:.3f}, {state['longitude']:.3f})")
        else:
            state["plan"] = [t for t in state["plan"] if t not in {"weather", "soil"}]
            _trace(state, f"dropping weather/soil from plan: {geo['error']}")

    runnable = []
    for t in state["plan"]:
        if t == "geocode":
            continue
        if t in {"weather", "soil"} and state.get("latitude") is None:
            _trace(state, f"skipping {t}: no coordinates")
            continue
        runnable.append(t)

    if runnable:
        results = await asyncio.gather(*[_execute(t, state) for t in runnable])
        outputs.update({r["tool"]: r for r in results})
    state["tool_outputs"] = outputs
    failed = [k for k, v in outputs.items() if not v.get("ok")]
    if failed:
        _trace(state, f"degraded tools {failed} — synthesizer will flag them")
    return state


# ------------------------------------------------------------ Synthesizer

SYNTH_SYSTEM = """You are AgriAdvisor, an expert agricultural assistant for Indian farmers.
You receive real-time tool outputs (weather / mandi prices / soil / agronomy passages).
Write practical, plain-language advice answering the farmer's question.

Rules:
1. Ground every number in the provided tool data — never invent prices, rainfall, or soil readings.
2. Lead with direct actionable advice (bullet points fine).
3. Add a short "Why?" section naming the data behind the advice (e.g. "11 mm rain Friday").
4. If a tool failed or returned nothing, clearly say so and give general best-practice advice with that caveat.
5. Keep it farmer-friendly: short sentences, no jargon.
6. Quote prices in Rs per quintal and mention mandi names.
7. If the question is a follow-up ("what about next week?"), use the conversation
   history to resolve references before answering.
"""


async def node_synthesizer(state: dict) -> dict:
    from langchain_core.prompts import ChatPromptTemplate
    from app.agent.llm import get_gemini

    blocks = []
    sources: list[str] = []
    for name, out in (state.get("tool_outputs") or {}).items():
        if out.get("ok"):
            blocks.append(f"### {name} data:\n{out.get('data')}")
            sources.append(name)
        else:
            blocks.append(f"### {name} data: UNAVAILABLE ({out.get('error', 'unknown error')})")

    rag_ctx = (state.get("tool_outputs") or {}).get("rag", {}).get("data")
    # rag data is a list of passages (tool wrapper only applies non-list results)
    if rag_ctx and isinstance(rag_ctx, dict):
        rag_ctx = rag_ctx.get("passages")
    if rag_ctx:
        passages = "\n".join(f"- {p}" for p in rag_ctx)
        blocks.append(f"### advisory passages:\n{passages}")

    context = "\n\n".join(blocks) or "No tool data available."
    history = _format_history(state.get("history"))
    lang_label = CODE_LABELS.get(state.get("detected_lang", "en"), "English")
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTH_SYSTEM),
        ("human",
         "Farmer's language: {lang}\nRecent conversation (for follow-ups):\n{history}\n"
         "Question:\n{query}\n\nLive data:\n{context}"),
    ])
    try:
        # single chained invoke: prompt formatting + LLM call in one thread hop
        chain = prompt | get_gemini()
        reply = await asyncio.to_thread(
            chain.invoke,
            {"lang": lang_label, "query": state["query"], "context": context, "history": history},
        )
        state["answer_en"] = _extract_text(reply)
        state["sources"] = sorted(set(sources))
        _trace(state, "synthesis complete; sources: " + ", ".join(state["sources"]))
    except Exception as exc:  # noqa: BLE001 — error_handler produces the fallback
        _trace(state, f"synthesizer LLM unavailable ({type(exc).__name__}) — routing to error handler")
        state["attempts"] = 1
    return state


# ------------------------------------------------------------ Error handler

async def node_error_handler(state: dict) -> dict:
    """Deterministic grounding check — if the LLM failed entirely, fall back."""
    if state.get("answer_en"):
        return state
    ok_tools = [k for k, v in (state.get("tool_outputs") or {}).items() if v.get("ok")]
    failed = [k for k, v in (state.get("tool_outputs") or {}).items() if not v.get("ok")]
    fallback_parts = []
    if ok_tools:
        for tool in ok_tools:
            data = state["tool_outputs"][tool]["data"]
            if tool == "weather" and data.get("summary"):
                fallback_parts.append(f"Weather ({data.get('location')}): {data['summary']}")
            elif tool == "mandi" and data.get("prices"):
                top = data["prices"][0]
                fallback_parts.append(
                    f"{data['commodity']}: modal 🔹 ₹{top['modal_price']}/quintal at {top['mandi']} mandi"
                )
            elif tool == "soil":
                fallback_parts.append(
                    f"Soil: pH {data.get('ph')}, N {data.get('nitrogen_kg_ha')} kg/ha, OC {data.get('organic_carbon_g_kg')} g/kg"
                )
            elif tool == "rag":
                passage_list = data.get("passages", data) if isinstance(data, dict) else data
                for p in passage_list:
                    fallback_parts.append(f"Advisory: {p['text'][:300]}")
    if fallback_parts:
        fallback = (
            "⚠️ The AI reasoning engine is temporarily unavailable — showing verified data directly:\n\n"
            + "\n".join(f"• {part}" for part in fallback_parts)
            + (f"\n\n(Tools checked: {', '.join(ok_tools)}; unavailable: {', '.join(failed)})" if failed else "")
        )
    else:
        fallback = (
            "⚠️ I couldn't fetch live data right now. Please retry shortly. "
            "General guidance: verify irrigation before spraying, and compare 2-3 nearby mandi prices before selling."
        )
    state["answer_en"] = fallback
    state["sources"] = ok_tools
    _trace(state, "error handler produced data-grounded fallback")
    return state
