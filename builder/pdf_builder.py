# builders/pdf_builder.py
import os
from .base_builder import BaseBuilder
from engine.video_processor import extract_frames_with_timestamps
from engine.transcript_parser import parse_srt_file
from engine.content_merger import match_frames_to_subs, merge_similar_segments
from PIL import Image

# --- GEREKLİ REPORTLAB IMPORTLARI (EKSİKLER EKLENDİ) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
# --- FONT DÜZELTMESİ İÇİN YENİ IMPORTLAR ---
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# --- IMPORT SONU ---


class PDFBuilder(BaseBuilder):

    def get_name(self) -> str:
        return "PDF Builder"

    def get_dir_name(self) -> str:
        return "pdf"  # output/job_name/pdf/ klasörü

    def _generate_pdf_prompt(self, transcript: str) -> str:
        return f"""
        GÖREV: ... (PDF için özel isteminiz buraya) ...
        HAM TRANSKRİPT: "{transcript}"
        """

    def _create_pdf_file(self, instruction_steps: list, output_path: str):
        print(f"[{self.job_name}] PDF dosyası oluşturuluyor: {output_path}")

        try:
            w, h = A4
            c = canvas.Canvas(output_path, pagesize=A4)
            styles = getSampleStyleSheet()

            # --- FONT DÜZELTMESİ (TÜRKÇE KARAKTER İÇİN) ---
            # reportlab ile gelen Vera fontunu (UTF-8 destekli) kaydediyoruz
            pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf'))

            style_n = styles['Normal']
            style_n.fontName = 'Vera'  # Stile fontu atıyoruz
            style_n.fontSize = 10
            style_n.spaceAfter = 10

            style_h = styles['Heading2']
            style_h.fontName = 'Vera'  # Stile fontu atıyoruz
            style_h.fontSize = 14
            style_h.spaceAfter = 15
            # --- FONT DÜZELTMESİ SONU ---

            margin = 50
            content_width = w - (2 * margin)

            for i, step in enumerate(instruction_steps):
                # 'Adım' metni artık 'Vera' fontu ile yazılacak
                p_title = Paragraph(f"Adım {i + 1}", style_h)
                p_title.wrapOn(c, content_width, margin)
                p_title.drawOn(c, margin, h - margin - 30)

                current_y = h - margin - 60

                # 1. Görüntü
                img_path = step['representative_png']
                try:
                    pil_img = Image.open(img_path)
                    img_w, img_h = pil_img.size
                    max_img_h = h / 3
                    scale = min(content_width / img_w, max_img_h / img_h)
                    new_w = img_w * scale
                    new_h = img_h * scale

                    c.drawImage(ImageReader(pil_img), margin, current_y - new_h, width=new_w, height=new_h,
                                preserveAspectRatio=True, anchor='nw')
                    current_y -= (new_h + 20)

                except Exception as e:
                    c.setFillColorRGB(1, 0, 0)  # Kırmızı renk
                    c.drawString(margin, current_y - 20, f"[Görüntü yüklenemedi: {img_path}]")
                    current_y -= 40

                # 2. AI Metni (Düzeltilmiş mock metni 'Vera' fontu ile yazılacak)
                ai_text = step['ai_generated_text'].replace('\n', '<br/>')
                p_text = Paragraph(ai_text, style_n)

                text_w, text_h = p_text.wrapOn(c, content_width, margin)

                if current_y - text_h < margin:
                    c.showPage()
                    current_y = h - margin
                    p_title.drawOn(c, margin, current_y - 30)
                    current_y -= 60

                p_text.drawOn(c, margin, current_y - text_h)

                c.showPage()

            c.save()
            print(f"[{self.job_name}] PDF başarıyla oluşturuldu ve diske kaydedildi.")

        except Exception as e:
            print(f"KRİTİK HATA: PDF dosyası oluşturulurken hata: {e}")
            raise e

    def build(self):
        # 1. Hammaddeleri al
        video_path = self.materials['video_path']
        srt_path = self.materials['srt_path']

        png_temp_folder = os.path.join(self.builder_output_dir, "screenshots")

        # 2. PDF'e özel iş akışını (workflow) çalıştır
        frames = extract_frames_with_timestamps(
            video_path,
            png_temp_folder,
            self.config.CAPTURE_INTERVAL_SEC
        )
        subs = parse_srt_file(srt_path)

        if not frames or not subs:
            raise ValueError("PDFBuilder: Video veya transkript işlenemedi.")

        matched = match_frames_to_subs(frames, subs)
        grouped = merge_similar_segments(
            matched,
            self.config.MIN_TEXT_LENGTH_FOR_GROUPING,
            self.config.IMAGE_SIMILARITY_THRESHOLD
        )

        final_instructions = []
        print(f"[{self.job_name}] {len(grouped)} grup için AI metni üretiyor...")

        for group in grouped:
            prompt = self._generate_pdf_prompt(group['combined_transcript'])

            # 4. Standart AI motorunu (Gemini veya Mock) çağır
            ai_text = self.ai_provider.generate_content(
                prompt,
                Image.open(group['representative_png'])
            )

            final_instructions.append({
                "representative_png": group['representative_png'],
                "ai_generated_text": ai_text
            })

        # 5. Son ürünü inşa et
        final_pdf_path = os.path.join(self.builder_output_dir, "Anlatim_Kitabi.pdf")
        self._create_pdf_file(final_instructions, final_pdf_path)