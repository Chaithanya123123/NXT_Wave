"""LLM factory (Gemini) + planner prompt."""

import functools

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.utils.config import GOOGLE_API_KEY


@functools.lru_cache(maxsize=1)
def get_gemini():
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY missing — set it in .env (aistudio.google.com)")
    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        max_retries=1,
    )


class Plan(BaseModel):
    """Which tools the agent should call to answer the farmer."""
    geocode: bool = Field(False, description="Location name needs resolving to coordinates")
    weather: bool = Field(False, description="Rain/irrigation/heat/digging/spraying decisions")
    mandi: bool = Field(False, description="Prices, selling, market timing questions")
    soil: bool = Field(False, description="Crop suitability, soil pH, fertilizer questions")
    rag: bool = Field(False, description="Pest, disease, sowing/harvest technique, general agronomy")
    crop: str = Field("", description="Crop name if mentioned/inferrable, else empty")


PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the planner of an agricultural advisory agent for Indian farmers.\n"
     "Decide which live data tools must run:\n"
     "- geocode: district/village names to coordinates (before weather/soil).\n"
     "- weather: 7-day local forecast (rain, temperature, humidity).\n"
     "- mandi: live per-quintal prices via Agmarknet.\n"
     "- soil: pH/nitrogen/texture via SoilGrids.\n"
     "- rag: expert agronomy passages (pest/disease/technique).\n"
     "Compound questions need multiple tools. Extract the crop name if stated. "
     "Answer with a Plan object only."),
    ("human", "Location hint: {location}\nFarmer question:\n{query}"),
])
