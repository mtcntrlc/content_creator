# builders/base_builder.py
import os
from abc import ABC, abstractmethod


class BaseBuilder(ABC):
    """
    Tüm içerik üreticilerinin uyması gereken standart arayüz.
    """

    def __init__(self, config, ai_provider, raw_materials: dict):
        self.config = config
        self.ai_provider = ai_provider
        self.materials = raw_materials  # Hammaddeler (video yolu, çıktı klasörü vb.)
        self.job_name = raw_materials.get("job_name", "unknown_job")

        # Her motorun, kendi çıktıları için özel bir klasör oluşturması gerekir (Madde 2)
        self.builder_output_dir = os.path.join(raw_materials.get("output_dir"), self.get_dir_name())
        os.makedirs(self.builder_output_dir, exist_ok=True)

        print(f"[{self.job_name}] Motor '{self.get_name()}' başlatıldı.")

    @abstractmethod
    def get_name(self) -> str:
        """Motorun adını döndürür (örn: 'PDF Builder')."""
        pass

    @abstractmethod
    def get_dir_name(self) -> str:
        """Çıktı klasör adını döndürür (örn: 'pdf')."""
        pass

    @abstractmethod
    def build(self):
        """Motorun ana üretim mantığı."""
        pass

    def run(self):
        """
Hata yönetimi için 'build'i kapsülleyen sarmalayıcı (Madde 7)
"""
        try:
            self.build()
        except Exception as e:
            # Hata oluşursa, hatayı yakala ve 'main.py'nin yakalaması için tekrar fırlat
            print(f"HATA: [{self.job_name}] -> '{self.get_name()}' motorunda: {e}")
            raise e  # Hatanın 'main.py' tarafından bilinmesini sağla