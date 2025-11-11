# engine/ai_mock.py
from PIL import Image
from .ai_base import BaseAIProvider
import time

class MockProvider(BaseAIProvider):
    """
    API anahtarı olmayan kullanıcılar için sahte AI sağlayıcı.
    API çağrısını taklit etmek için 1 saniye bekler.
    """
    def get_name(self) -> str:
        return "Mock Provider (Test Modu)"

    def generate_content(self, prompt: str, image: Image.Image = None) -> str:
        time.sleep(1) # Sahte bir ağ gecikmesi
        return (
            "[MOCK AI CEVABI]\n"
            "1. Bu, AI tarafından üretilmiş sahte bir adımdır.\n"
            "2. Projenin API anahtarı olmadan çalıştığını gösterir."
        )