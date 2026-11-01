"""High-level agent orchestration — glue between API/UI and LangGraph pipeline."""

from typing import AsyncIterator

from app.tools.rag_tool import ingest_docs
from app.utils.language import detect_language
from app.agent.state import AgentState


def _build_state(
    query: str,
    location_hint: str | None,
    latitude: float | None,
    longitude: float | None,
    declared_lang: str | None,
    crop_hint: str | None,
    history: list[dict] | None,
) -> tuple[AgentState, object]:
    detected = detect_language(query, declared_lang)
    state: AgentState = {
        "query": query,
        "detected_lang": detected.code,
        "declared_lang": declared_lang,
        "location_hint": location_hint,
        "crop_hint": crop_hint,
        "history": (history or [])[-6:],  # last 3 Q&A turns
        "tool_outputs": {},
        "reasoning_trace": [],
        "sources": [],
    }
    if latitude is not None and longitude is not None:
        state["latitude"] = latitude
        state["longitude"] = longitude
        state["location_name"] = location_hint or "provided coordinates"
    return state, detected


def _final_result(query: str, detected, answer: dict) -> dict:
    return {
        "query": query,
        "detected_language": detected.label,
        "detected_lang_code": detected.code,
        "plan": answer.get("plan", []),
        "answer": answer.get("answer_lang") or answer.get("answer_en", ""),
        "reasoning_trace": answer.get("reasoning_trace", []),
        "sources": answer.get("sources", []),
        "tool_outputs": {
            k: v for k, v in (answer.get("tool_outputs") or {}).items()
        },
    }


async def answer_query(
    query: str,
    location_hint: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    declared_lang: str | None = None,
    crop_hint: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    from app.agent.graph import run_agent  # lazy: graph only compiled when used

    state, detected = _build_state(
        query, location_hint, latitude, longitude, declared_lang, crop_hint, history
    )
    answer = await run_agent(state)
    return _final_result(query, detected, answer)


async def stream_query(
    query: str,
    location_hint: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    declared_lang: str | None = None,
    crop_hint: str | None = None,
    history: list[dict] | None = None,
) -> AsyncIterator[dict]:
    """
    Same pipeline as answer_query, but yields NDJSON-friendly events as the
    agent progresses: {"type":"trace","line":...} then {"type":"done","result":...}.
    """
    from app.agent.graph import compiled_graph  # lazy import

    state, detected = _build_state(
        query, location_hint, latitude, longitude, declared_lang, crop_hint, history
    )
    final_state: AgentState = state
    emitted = 0
    async for full in compiled_graph.astream(state, stream_mode="values"):
        final_state = full
        trace = full.get("reasoning_trace") or []
        for line in trace[emitted:]:
            yield {"type": "trace", "line": line}
        emitted = len(trace)
    yield {"type": "done", "result": _final_result(query, detected, final_state)}


def ensure_knowledge_base():
    try:
        ingest_docs()
    except Exception as exc:  # noqa: BLE001
        print(f"[knowledge_base] warning: {exc}")
