from typing import Annotated, Any, TypedDict


def merge_tool_outputs(left: dict, right: dict) -> dict:
    """Reducer: accumulate tool outputs by tool name."""
    if right:
        merged = dict(left or {})
        merged.update(right)
        return merged
    return left


class AgentState(TypedDict, total=False):
    # Inputs
    query: str
    detected_lang: str
    declared_lang: str | None
    location_hint: str | None
    crop_hint: str | None
    history: list  # recent Q&A turns for follow-up questions

    # Working memory
    location_name: str | None
    latitude: float | None
    longitude: float | None
    plan: list[str]
    tool_outputs: Annotated[dict[str, Any], merge_tool_outputs]
    retrieved_context: list[dict]
    attempts: int

    # Outputs
    answer_en: str
    answer_lang: str
    reasoning_trace: list[str]
    sources: list[str]
    audio_b64: str | None
    error: str | None
