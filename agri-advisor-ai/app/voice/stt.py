import httpx

from app.utils.config import SARVAM_API_KEY

STT_URL = "https://api.sarvam.ai/speech-to-text"

# Sarvam expects BCP-47 language codes
_BCP47 = {
    "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN", "mr": "mr-IN", "kn": "kn-IN",
    "bn": "bn-IN", "gu": "gu-IN", "ml": "ml-IN", "pa": "pa-IN", "or": "od-IN",
    "as": "as-IN", "en": "en-IN",
}


async def transcribe(audio_bytes: bytes, audio_format: str = "wav", lang_hint: str | None = None) -> str:
    """
    Speech-to-text (Saaras v4). Accepts regional-language audio, returns
    the transcript in the spoken language (auto-detected when no hint).
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY missing")
    headers = {"api-subscription-key": SARVAM_API_KEY}
    files = {"file": (f"audio.{audio_format}", audio_bytes, f"audio/{audio_format}")}
    data = {"model": "saaras:v4", "mode": "transcribe"}
    if lang_hint:
        data["language_code"] = _BCP47.get(lang_hint[:2].lower(), "unknown")
    else:
        data["language_code"] = "unknown"

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(STT_URL, headers=headers, files=files, data=data)
        if r.status_code >= 400:
            raise RuntimeError(f"STT HTTP {r.status_code}: {r.text[:500]}")
        payload = r.json()
    return payload.get("transcript", "") or payload.get("text", "")
