# config.py
import os
from dotenv import load_dotenv

# 1. .env dosyasını yükle
load_dotenv()

# 2. Güvenli API Anahtarı Okuması (Madde 1)
API_ANAHTARI = os.environ.get("GOOGLE_API_KEY")

# 3. AI Sağlayıcı Seçimi (Madde 4)
# .env'de belirtilmemişse, güvenli mod olan "MOCK"u varsay
AI_PROVIDER_TYPE = os.environ.get("AI_PROVIDER_TYPE", "MOCK")
AI_MODEL_NAME = "gemini-1.5-pro" # (Gemini kullanılıyorsa)

# 4. İş Bazlı Girdi/Çıktı Klasörleri (Madde 2)
INPUT_DIR = "input"
OUTPUT_DIR = "output"

# 5. Çalıştırılacak Motorlar (Fabrika Modeli)
BUILDERS_TO_RUN = [
    "PDF",
    # "CAROUSEL", # Hazır olduğunda buraya ekle
    # "REELS",    # Hazır olduğunda buraya ekle
]

# 6. Motor Parametreleri (PDFBuilder bunları okuyacak)
CAPTURE_INTERVAL_SEC = 5
MIN_TEXT_LENGTH_FOR_GROUPING = 25
IMAGE_SIMILARITY_THRESHOLD = 5