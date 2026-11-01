from fastapi import Depends, FastAPI, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import base64
import json as _json
import traceback
from pathlib import Path

from app.agent.service import answer_query, ensure_knowledge_base, stream_query
from app.utils.config import DATA_GOV_API_KEY
from app.voice.stt import transcribe
from app.voice.tts import synthesize_speech

app = FastAPI(title="AgriAdvisor AI", version="1.0.0",
              description="Multilingual agritech advisory agent — Forge Buildathon")

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.on_event("startup")
def _startup() -> None:
    ensure_knowledge_base()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str = Field(..., description="Farmer's question, any language")
    location_hint: str | None = Field(None, examples=["Kurnool"])
    latitude: float | None = None
    longitude: float | None = None
    declared_lang: str | None = Field(None, examples=["te", "hindi"])
    crop_hint: str | None = None
    history: list[dict] | None = Field(
        None, description="Last few turns: [{'role':'user'|'assistant','content':...}]"
    )


@app.get("/health")
def health():
    import os

    def _configured(v: str) -> bool:
        return bool(v) and not v.lower().startswith("your_")
    return {
        "status": "ok",
        "keys": {"google": _configured(os.getenv("GOOGLE_API_KEY", ""))},
        "data_gov_key": _configured(DATA_GOV_API_KEY),
    }


@app.post("/ask")
async def ask(req: AskRequest):
    """Main advisory endpoint — plans + fetches live data, reasons, replies."""
    try:
        if not req.query or not req.query.strip():
            raise HTTPException(400, "empty query")
        result = await answer_query(
            req.query,
            req.location_hint,
            req.latitude,
            req.longitude,
            req.declared_lang,
            req.crop_hint,
            req.history,
        )
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return JSONResponse(status_code=500, content={
            "error": f"{type(exc).__name__}: {exc}",
            "detail": "agent pipeline failed — retry or use a more specific question",
        })


@app.post("/ask/stream")
async def ask_stream(req: AskRequest):
    """Streaming variant of /ask — NDJSON events:
    {"type":"trace","line":...} as the agent works, then
    {"type":"done","result":<same shape as /ask>}."""

    async def _gen():
        try:
            if not req.query or not req.query.strip():
                yield _json.dumps({"type": "error", "error": "empty query"}) + "\n"
                return
            async for event in stream_query(
                req.query,
                req.location_hint,
                req.latitude,
                req.longitude,
                req.declared_lang,
                req.crop_hint,
                req.history,
            ):
                yield _json.dumps(event, ensure_ascii=False, default=str) + "\n"
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            yield _json.dumps({"type": "error", "error": f"{type(exc).__name__}: {exc}"}) + "\n"

    return StreamingResponse(_gen(), media_type="application/x-ndjson")


@app.post("/transcribe")
async def transcribe_endpoint(
    audio: UploadFile,
    lang_hint: str | None = None,
):
    """Speech-to-text: regional audio → transcript."""
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(400, "empty audio file")
        text = await transcribe(audio_bytes, lang_hint=lang_hint)
        return {"transcript": text}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return JSONResponse(status_code=502, content={"error": f"STT failed: {exc}"})


class TtsRequest(BaseModel):
    text: str
    lang_code: str = Field("en", examples=["te", "hi"])


@app.post("/tts")
async def tts_endpoint(req: TtsRequest):
    """Text-to-speech: advice text → base64 WAV audio in farmer's language."""
    try:
        audio_b64 = await synthesize_speech(req.text, req.lang_code)
        if not audio_b64:
            raise HTTPException(502, "no audio generated")
        audio_bytes = base64.b64decode(audio_b64)
        from fastapi.responses import Response
        return Response(content=audio_bytes, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return JSONResponse(status_code=502, content={"error": f"TTS failed: {exc}"})


@app.get("/kb/stats")
def kb_stats():
    from app.tools.rag_tool import _get_collection
    col = _get_collection()
    return {"vector_count": col.count()}


# ---------------------------------------------------------------------------
# React frontend (built with `npm run build` in frontend/)
# ---------------------------------------------------------------------------
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def frontend_index():
        return FileResponse(FRONTEND_DIST / "index.html")
