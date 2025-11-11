# engine/transcript_parser.py
import re
from typing import List, Dict, Any
import os


def _time_to_seconds(time_str: str) -> float:
    """SRT zaman damgasını (örn: 00:01:15,345) saniyeye çevirir."""
    try:
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    except ValueError as e:
        print(f"Hata: Beklenmeyen SRT zaman formatı '{time_str}'. Hata: {e}")
        return 0.0


def parse_srt_file(srt_path: str) -> List[Dict[str, Any]]:
    """
    Bir .srt dosyasını okur ve zaman damgalı metin segmentlerinin
    bir listesini döndürür.

    Args:
        srt_path (str): İşlenecek .srt dosyasının tam yolu.

    Returns:
        List[Dict[str, Any]]: Her biri {'start_sec': float, 'end_sec': float, 'text': str}
                              içeren sözlüklerin listesi.
    """

    transcript_segments = []

    # Hata Yönetimi (Madde 7)
    if not os.path.exists(srt_path):
        print(f"Hata: Transkript dosyası bulunamadı - {srt_path}")
        return []

    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Hata: Transkript dosyası okunamadı - {srt_path}. Hata: {e}")
        return []

    # .srt formatını yakalamak için regex deseni
    # (Boş satırlar ve satır sonları konusunda daha esnek)
    pattern = re.compile(
        r'\d+\s*'  # Segment numarası
        r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*'  # Zaman damgaları
        r'(.+?)\s*'  # Metin içeriği (tembel eşleşme)
        r'(?=\n\n|\n\d+\n|\Z)',  # Bir sonraki bloğa kadar oku (çift satır sonu, yeni segment no, veya dosya sonu)
        re.DOTALL | re.MULTILINE
    )

    print(f"  [Transkript İşlemci] '{srt_path}' ayrıştırılıyor...")

    match_count = 0
    for match in pattern.finditer(content):
        try:
            start_time_str, end_time_str, text = match.groups()

            transcript_segments.append({
                "start_sec": _time_to_seconds(start_time_str),
                "end_sec": _time_to_seconds(end_time_str),
                "text": text.strip().replace('\n', ' ')  # Metni temizle
            })
            match_count += 1
        except Exception as e:
            print(f"Uyarı: SRT segmenti ayrıştırılamadı. Metin: '{text}'. Hata: {e}")

    if match_count == 0:
        print(f"Uyarı: '{srt_path}' dosyasında geçerli transkript segmenti bulunamadı.")
        return []

    print(f"  [Transkript İşlemci] Tamamlandı. {len(transcript_segments)} segment bulundu.")
    return transcript_segments