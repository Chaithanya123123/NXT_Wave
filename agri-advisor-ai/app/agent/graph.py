"""LangGraph pipeline definition — the full agentic loop."""

import asyncio

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    node_error_handler,
    node_execute_tools,
    node_planner,
    node_synthesizer,
)

_CODE_NAMES = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil",
    "mr": "Marathi", "kn": "Kannada", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi", "ml": "Malayalam", "or": "Odia", "as": "Assamese",
}


async def node_translate(state: AgentState) -> AgentState:
    """Render the final answer in the farmer's language (LLM translation)."""
    lang = state.get("detected_lang", "en") or "en"
    if lang == "en" or not state.get("answer_en"):
        state["answer_lang"] = state.get("answer_en", "")
        return state
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from app.agent.llm import get_gemini

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an interpreter for Indian farmers. Translate the advisory into {lang}. "
             "Keep all numbers, mandi names, and bullet structure intact. Simple words only."),
            ("human", "{text}"),
        ])
        llm = get_gemini()
        msgs = prompt.invoke({"lang": _CODE_NAMES.get(lang, lang), "text": state["answer_en"]})
        reply = await asyncio.to_thread(llm.invoke, msgs)
        from app.agent.nodes import _extract_text

        state["answer_lang"] = _extract_text(reply)
    except Exception:  # noqa: BLE001 — fall back to English answer
        state["answer_lang"] = state["answer_en"]
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("planner", node_planner)
    graph.add_node("tools", node_execute_tools)
    graph.add_node("synthesizer", node_synthesizer)
    graph.add_node("error_handler", node_error_handler)
    graph.add_node("translate", node_translate)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "tools")
    graph.add_edge("tools", "synthesizer")
    graph.add_conditional_edges(
        "synthesizer",
        lambda s: "translate" if s.get("answer_en") else "error_handler",
        {"translate": "translate", "error_handler": "error_handler"},
    )
    graph.add_edge("error_handler", "translate")
    graph.add_edge("translate", END)
    return graph.compile()


compiled_graph = build_graph()


async def run_agent(state: AgentState) -> AgentState:
    return await compiled_graph.ainvoke(state)
