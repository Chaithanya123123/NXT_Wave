from dataclasses import dataclass

from langdetect import detect as _detect
from langdetect import detect_langs

LANG_NAME_TO_CODE = {
    "english": "en", "hindi": "hi", "telugu": "te", "tamil": "ta",
    "marathi": "mr", "kannada": "kn", "bengali": "bn", "gujarati": "gu",
    "punjabi": "pa", "malayalam": "ml", "odia": "or", "assamese": "as",
}

CODE_TO_LABEL = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil",
    "mr": "Marathi", "kn": "Kannada", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi", "ml": "Malayalam", "or": "Odia", "as": "Assamese",
}


@dataclass
class DetectedLanguage:
    code: str
    label: str
    confidence: float


def detect_language(text: str, declared_lang: str | None = None) -> DetectedLanguage:
    if declared_lang:
        code = LANG_NAME_TO_CODE.get(declared_lang.lower().strip(), None)
        if code is None:
            code = declared_lang.lower()[:2]
        return DetectedLanguage(code, CODE_TO_LABEL.get(code, declared_lang.title()), 1.0)
    try:
        best = detect_langs(text)[0]
        code = best.lang
    except Exception:
        code, conf = "en", 0.0
        try:
            code = _detect(text) or "en"
        except Exception:
            pass
        return DetectedLanguage(code, CODE_TO_LABEL.get(code, code.upper()), conf)
    return DetectedLanguage(code, CODE_TO_LABEL.get(code, code.upper()), best.prob)
