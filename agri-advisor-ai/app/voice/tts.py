import base64
import httpx

from app.utils.config import SARVAM_API_KEY

TTS_URL = "https://api.sarvam.ai/text-to-speech"

LANG_TO_SPEAK = {
    "en": "en-US", "hi": "hi-IN", "te": "te-IN", "ta": "ta-IN",
    "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN", "kn": "kn-IN",
    "ml": "ml-IN", "pa": "pa-IN", "od": "od-IN",
}


async def synthesize_speech(text: str, lang_code: str = "en", max_len: int = 1500) -> str:
    """
    Text-to-speech in the farmer's language.
    Returns base64-encoded WAV audio.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY missing")
    if len(text) > max_len:
        text = text[:max_len] + "…"
    headers = {"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"}
    body = {
        "inputs": [text],
        "target_language_code": LANG_TO_SPEAK.get(lang_code, "en-IN"),
        "model": "bulbul:v3",
        "speech_sample_rate": 22050,
        "encode_audio_as_compressed_waveform": True,
        "audio_as_wav": True,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(TTS_URL, headers=headers, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"TTS HTTP {r.status_code}: {r.text[:500]}")
        payload = r.json()
    audios = payload.get("audios") or []
    return audios[0] if audios else ""
