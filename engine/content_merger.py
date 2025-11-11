# engine/content_merger.py
from PIL import Image
import imagehash
from typing import List, Dict, Any
import os


# --- Yardımcı Fonksiyon (Dışarıdan erişilmez) ---
def _calculate_phash(image_path: str):
    """Bir resmin perceptual hash (pHash) değerini hesaplar."""
    try:
        if not os.path.exists(image_path):
            print(f"Uyarı: pHash için resim bulunamadı: {image_path}")
            return None
        return imagehash.phash(Image.open(image_path))
    except Exception as e:
        # Hata Yönetimi: Bozuk resim dosyaları vb.
        print(f"Uyarı: Hash hesaplama hatası ({image_path}). Resim bozuk olabilir. Hata: {e}")
        return None


# --- Ana Fonksiyon 1: Eşleştirme ---
def match_frames_to_subs(frames: List[Dict[str, Any]], subs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    PNG'leri (frame) zaman damgalarına göre transkript segmentleriyle eşleştirir.

    Returns:
        List[Dict[str, Any]]: {'file_path', 'timestamp_sec', 'transcript'} listesi.
    """
    print("  [İçerik Birleştirici] Kareler ve transkriptler eşleştiriliyor...")
    matched_data = []

    for frame in frames:
        ts = frame['timestamp_sec']
        found_sub = ""
        for sub in subs:
            # PNG'nin zaman damgası, transkriptin aralığına düşüyor mu?
            if sub['start_sec'] <= ts <= sub['end_sec']:
                found_sub = sub['text']
                break

        frame['transcript'] = found_sub
        matched_data.append(frame)

    print(f"  [İçerik Birleştirici] Eşleştirme tamamlandı. {len(matched_data)} eşleşme.")
    return matched_data


# --- Ana Fonksiyon 2: Birleştirme (Gruplama) ---
def merge_similar_segments(
        matched_data: List[Dict[str, Any]],
        min_text_length: int,
        image_similarity_threshold: int
) -> List[Dict[str, Any]]:
    """
    Benzer PNG'leri veya kısa metinleri olan adımları tek bir grupta birleştirir.
    Bu, PDF veya Blog motorları için kullanışlıdır.

    Returns:
        List[Dict[str, Any]]: {'representative_png', 'combined_transcript'} listesi.
    """
    print("  [İçerik Birleştirici] Benzer/kısa segmentler gruplanıyor...")
    if not matched_data:
        return []

    grouped_steps = []

    # Başlangıç
    current_group_png = matched_data[0]['file_path']
    current_group_transcript = [matched_data[0]['transcript']]
    last_valid_hash = _calculate_phash(current_group_png)

    for i in range(1, len(matched_data)):
        current_item = matched_data[i]
        current_text = current_item['transcript']
        current_png_path = current_item['file_path']
        current_hash = _calculate_phash(current_png_path)

        # 1. Metin çok mu kısa?
        is_text_too_short = len(current_text) < min_text_length

        # 2. Görüntü bir öncekine çok mu benziyor?
        is_image_too_similar = False
        if last_valid_hash and current_hash:
            hash_diff = last_valid_hash - current_hash
            if hash_diff <= image_similarity_threshold:
                is_image_too_similar = True

        # Koşul: Eğer metin çok kısaysa VEYA görüntü bir öncekine çok benziyorsa,
        # bu adımı mevcut grupla birleştir.
        if is_text_too_short or is_image_too_similar:
            current_group_transcript.append(current_text)
            # (PNG'yi değiştirmiyoruz, mevcut PNG'yi temsilci olarak tutuyoruz)

        # Koşul: Eğer bu adım anlamlıysa (metin yeterli VE görüntü farklı),
        # mevcut grubu kaydet ve yeni bir grup başlat.
        else:
            # Mevcut grubu kaydet
            grouped_steps.append({
                "representative_png": current_group_png,
                "combined_transcript": " ".join(filter(None, current_group_transcript))
            })

            # Yeni grubu başlat
            current_group_png = current_png_path
            current_group_transcript = [current_text]
            last_valid_hash = current_hash  # Yeni temsilci hash

    # Döngüden sonra kalan son grubu da ekle
    grouped_steps.append({
        "representative_png": current_group_png,
        "combined_transcript": " ".join(filter(None, current_group_transcript))
    })

    print(
        f"  [İçerik Birleştirici] Gruplama tamamlandı. {len(matched_data)} orijinal adım, {len(grouped_steps)} anlamlı gruba indirgendi.")
    return grouped_steps