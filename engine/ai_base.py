# engine/ai_base.py
from abc import ABC, abstractmethod
from PIL import Image


class BaseAIProvider(ABC):
    """
    Tüm AI sağlayıcılarının uyması gereken standart.
    (Gemini, Mock, GPT, Claude vb.)
    """

    def __init__(self, config):
        self.config = config
        print(f"[AI Sağlayıcı] {self.get_name()} başlatıldı.")

    @abstractmethod
    def get_name(self) -> str:
        """Sağlayıcının adını döndürür."""
        pass

    @abstractmethod
    def generate_content(self, prompt: str, image: Image.Image = None) -> str:
        """
        AI modelinden metin veya görsel-metin yanıtı alır.
        Görsel (image) opsiyoneldir.
        """
        pass