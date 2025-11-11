# main.py
import config
import os
import json
import time
from datetime import datetime

# AI Sağlayıcıları
from engine.ai_base import BaseAIProvider
from engine.ai_gemini import GeminiProvider
from engine.ai_mock import MockProvider

# Motor (Builder) Sınıfları
from builder.pdf_builder import PDFBuilder

# ... (Gelecekte diğer builder'lar buraya eklenecek)

AVAILABLE_BUILDERS = {
    "PDF": PDFBuilder,
    # "CAROUSEL": CarouselBuilder,
}

AVAILABLE_AI_PROVIDERS = {
    "GEMINI": GeminiProvider,
    "MOCK": MockProvider,
}


def setup_ai_provider() -> BaseAIProvider:
    """Config'e göre doğru AI sağlayıcıyı seçer ve başlatır."""
    provider_name = config.AI_PROVIDER_TYPE

    if provider_name not in AVAILABLE_AI_PROVIDERS:
        print(f"Hata: '{provider_name}' geçerli bir AI sağlayıcı değil. 'MOCK' kullanılacak.")
        provider_name = "MOCK"

    if provider_name == "GEMINI" and not config.API_ANAHTARI:
        print("Uyarı: 'GEMINI' seçildi ancak API anahtarı bulunamadı. 'MOCK' kullanılacak.")
        provider_name = "MOCK"

    ProviderClass = AVAILABLE_AI_PROVIDERS[provider_name]
    return ProviderClass(config)


def update_status(status_file: str, genel_durum: str, motor: str = None, motor_durum: str = None, hata_mesaji: str = None):
    """
    status.json dosyasını okur, günceller ve yazar. (Madde 3: Durum Yönetimi)
    """
    status_data = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
        except json.JSONDecodeError:
            pass # Dosya bozuksa üzerine yaz

    status_data["genel_durum"] = genel_durum # genel_durum'u kullan
    status_data["son_guncelleme"] = datetime.now().isoformat()

    if motor and motor_durum: # motor_durum'u kontrol et
        if "calisan_motorlar" not in status_data:
            status_data["calisan_motorlar"] = {}
        status_data["calisan_motorlar"][motor] = motor_durum # motor_durum'u ata

    if hata_mesaji:
        status_data["hata_mesaji"] = hata_mesaji

    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"KRİTİK HATA: Durum dosyası yazılamadı! {status_file}. Hata: {e}")


def main_factory():
    print("--- İçerik Fabrikası Başlatıldı ---")

    # 1. AI Sağlayıcıyı bir kez kur
    try:
        ai_provider = setup_ai_provider()
    except Exception as e:
        print(f"Kritik Hata: AI Sağlayıcı başlatılamadı. {e}")
        return

    # 2. İşleri (Jobs) Tara (Madde 2: İş Bazlı Hiyerarşi)
    for job_name in os.listdir(config.INPUT_DIR):
        job_input_dir = os.path.join(config.INPUT_DIR, job_name)
        job_output_dir = os.path.join(config.OUTPUT_DIR, job_name)

        if not os.path.isdir(job_input_dir):
            continue  # Klasör değilse atla

        # 3. Durum (State) Kontrolü (Madde 3)
        status_file = os.path.join(job_output_dir, "status.json")
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    if json.load(f).get("genel_durum") == "TAMAMLANDI":
                        print(f"'{job_name}' zaten işlenmiş. Atlanıyor.")
                        continue
            except:
                pass  # Bozuk status dosyası, yeniden işle

        print(f"\n--- Yeni İş Başlatıldı: '{job_name}' ---")
        os.makedirs(job_output_dir, exist_ok=True)
        update_status(status_file, genel_durum="İŞLENİYOR")

        # 4. Hammaddeleri Hazırla (Her iş için özel)
        try:
            # (Streamlit için bu bölümü daha esnek hale getireceğiz,
            # şimdilik video/transkript varsayıyoruz)
            video_path = os.path.join(job_input_dir, "video.mp4")
            srt_path = os.path.join(job_input_dir, "transkript.srt")

            if not os.path.exists(video_path) or not os.path.exists(srt_path):
                raise FileNotFoundError(f"Girdi dosyaları bulunamadı: video.mp4 veya transkript.srt eksik.")

            raw_materials = {
                "job_name": job_name,
                "input_dir": job_input_dir,
                "output_dir": job_output_dir,
                "video_path": video_path,
                "srt_path": srt_path,
            }
        except Exception as e:
            print(f"Hata: '{job_name}' için hammaddeler hazırlanamadı. Hata: {e}")
            update_status(status_file, genel_durum="HATA", hata_mesaji=str(e))
            continue  # Sonraki işe geç

        # 5. Üretim Hattını (Builder'ları) Çalıştır
        try:
            for builder_name in config.BUILDERS_TO_RUN:
                if builder_name in AVAILABLE_BUILDERS:
                    print(f"[{job_name}] -> '{builder_name}' motoru çalıştırılıyor...")
                    BuilderClass = AVAILABLE_BUILDERS[builder_name]
                    builder_instance = BuilderClass(config, ai_provider, raw_materials)

                    # 7. Hata Yönetimi (Madde 7)
                    builder_instance.run()  # Builder'ın kendi içindeki build() metodunu çağırır
                    update_status(status_file, genel_durum="İŞLENİYOR", motor=builder_name, motor_durum="BAŞARILI")
                else:
                    print(f"Uyarı: '{builder_name}' motoru bulunamadı.")

            update_status(status_file, genel_durum="TAMAMLANDI")
            print(f"--- İş Başarıyla Tamamlandı: '{job_name}' ---")

        except Exception as e:
            # 7. Hata Yönetimi (Genel)
            print(f"!! KRİTİK HATA: '{job_name}' işlenirken çöktü. Hata: {e}")
            update_status(status_file, genel_durum="HATA", hata_mesaji=str(e))


if __name__ == "__main__":
    main_factory()