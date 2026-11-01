import os

from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY", "")

# External API endpoints
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1/search"
SOILGRIDS_BASE = "https://rest.isric.org/soilgrids/v2.0/properties/query"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
AGMARKNET_BASE = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

UA = "AgriAdvisorAI/1.0 (Forge Hackathon project)"
