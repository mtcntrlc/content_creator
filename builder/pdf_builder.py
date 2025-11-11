# builders/pdf_builder.py
import os
from .base_builder import BaseBuilder
from engine.video_processor import extract_frames_with_timestamps
from engine.transcript_parser import parse_srt_file
from engine.content_merger import match_frames_to_subs, merge_similar_segments
from PIL import Image
from reportlab.pdfgen import canvas  # ... (ve diğer reportlab importları)
from reportlab.lib.pagesizes import A4


# ... (PDF_Builder için gereken diğer tüm importlar)

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
        # ... (Geçen seferki 'create_instructional_pdf' fonksiyonunun
        # tüm reportlab kodunu buraya taşıyın) ...
        # ... (c.save() vb.) ...
        print(f"[{self.job_name}] PDF başarıyla oluşturuldu.")

    def build(self):
        # 1. Hammaddeleri al
        video_path = self.materials['video_path']
        srt_path = self.materials['srt_path']

        # Bu motora özel PNG klasörü (Madde 2)
        # output/ornek_proje_1/pdf/screenshots/
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