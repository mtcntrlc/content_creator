# engine/ai_gemini.py
import google.generativeai as genai
from PIL import Image
from .ai_base import BaseAIProvider


class GeminiProvider(BaseAIProvider):

    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.API_ANAHTARI
        self.model_name = config.AI_MODEL_NAME
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            raise ValueError(f"Gemini modeli başlatılamadı. API anahtarınızı kontrol edin. Hata: {e}")

    def get_name(self) -> str:
        return "Google Gemini"

    def generate_content(self, prompt: str, image: Image.Image = None) -> str:
        try:
            if image:
                response = self.model.generate_content([prompt, image])
            else:
                response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Hata: Gemini API çağrısı başarısız oldu. Hata: {e}")
            return f"[Gemini Hatası: {e}]"