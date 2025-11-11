# engine/video_processor.py
import cv2
import os
from typing import List, Dict, Any


def extract_frames_with_timestamps(video_path: str, output_folder: str, interval_seconds: int = 5) -> List[
    Dict[str, Any]]:
    """
    Belirtilen aralıklarla videodan kareler çıkarır ve her karenin dosya yolunu ve
    zaman damgasını (saniye) içeren bir liste döndürür.

    Args:
        video_path (str): İşlenecek video dosyasının tam yolu.
        output_folder (str): PNG'lerin kaydedileceği klasörün tam yolu.
        interval_seconds (int): Kareler arasındaki saniye cinsinden aralık.

    Returns:
        List[Dict[str, Any]]: Her biri {'file_path': str, 'timestamp_sec': float}
                              içeren sözlüklerin listesi.
    """

    # Hata Yönetimi (Madde 7)
    if not os.path.exists(video_path):
        print(f"Hata: Video dosyası bulunamadı - {video_path}")
        return []

    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder)
        except OSError as e:
            print(f"Hata: Çıktı klasörü oluşturulamadı - {output_folder}. Hata: {e}")
            return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Hata: Video dosyası açılamadı (bozuk olabilir) - {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)

    # Hata Yönetimi: Geçersiz FPS
    if fps == 0:
        print(f"Hata: Video FPS değeri okunamadı (0). - {video_path}")
        cap.release()
        return []

    frame_interval = int(fps * interval_seconds)  # Kare sayısı olarak aralık
    frame_count = 0
    saved_count = 0

    frame_data = []

    print(f"  [Video İşlemci] '{video_path}' işleniyor (Her {interval_seconds} saniyede 1 kare)...")

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break  # Video bitti veya okuma hatası

        if frame_count % frame_interval == 0:
            current_time_sec = frame_count / fps
            frame_filename = os.path.join(output_folder, f"frame_{saved_count:05d}.png")

            try:
                cv2.imwrite(frame_filename, frame)
            except Exception as e:
                print(f"Uyarı: Kare {saved_count} diske yazılamadı. Atlanıyor. Hata: {e}")
                continue  # Diske yazamazsak listeye ekleme

            frame_data.append({
                "file_path": frame_filename,
                "timestamp_sec": current_time_sec
            })
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"  [Video İşlemci] Tamamlandı. {saved_count} PNG kaydedildi.")
    return frame_data