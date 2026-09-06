import io
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

class ParsedPDF:
    def __init__(
        self,
        filename: str,
        page_count: int,
        text_by_page: Dict[int, str],
        tables_by_page: Dict[int, List[str]],
        images: List[Dict[str, Any]],
        flavor: str,
        detected_language: str,
        raw_doc: fitz.Document,
        blocks_by_page: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ):
        self.filename = filename
        self.page_count = page_count
        self.text_by_page = text_by_page
        self.tables_by_page = tables_by_page
        self.images = images
        self.flavor = flavor
        self.detected_language = detected_language
        self._raw_doc = raw_doc
        self.blocks_by_page = blocks_by_page or {}

    @property
    def full_text(self) -> str:
        return "\n\n".join([f"--- PAGE {p} ---\n{t}" for p, t in self.text_by_page.items()])

    @property
    def full_content_with_tables(self) -> str:
        out = []
        for p in range(1, self.page_count + 1):
            out.append(f"--- PAGE {p} ---")
            text = self.text_by_page.get(p, "").strip()
            if text:
                out.append(text)
            tables = self.tables_by_page.get(p, [])
            if tables:
                out.append("\n[STRUCTURED TABLES ON PAGE " + str(p) + "]:\n" + "\n\n".join(tables))
        return "\n\n".join(out)

    def render_page_image(self, page_num: int = 1, dpi: int = 150) -> Image.Image:
        """Renders a PDF page to a PIL Image (useful for scanned/handwritten docs)."""
        idx = max(0, min(page_num - 1, self.page_count - 1))
        page = self._raw_doc[idx]
        pix = page.get_pixmap(dpi=dpi)
        img_bytes = pix.tobytes("png")
        return Image.open(io.BytesIO(img_bytes))


class PDFParser:
    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "document.pdf") -> ParsedPDF:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        text_by_page: Dict[int, str] = {}
        tables_by_page: Dict[int, List[str]] = {}
        blocks_by_page: Dict[int, List[Dict[str, Any]]] = {}
        extracted_images: List[Dict[str, Any]] = []

        total_chars = 0
        all_text_combined = ""

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            
            # Extract plain text
            page_text = page.get_text("text") or ""
            text_by_page[page_num] = page_text
            total_chars += len(page_text.strip())
            all_text_combined += " " + page_text

            # Extract text blocks with visual bounding box coordinates
            page_blocks: List[Dict[str, Any]] = []
            try:
                for b in page.get_text("blocks"):
                    if b[6] == 0 and b[4].strip():  # text block
                        page_blocks.append({
                            "bbox": (float(b[0]), float(b[1]), float(b[2]), float(b[3])),
                            "text": b[4].strip(),
                            "block_no": int(b[5])
                        })
            except Exception:
                pass
            blocks_by_page[page_num] = page_blocks

            # Extract structured tables
            page_tables: List[str] = []
            try:
                tabs = page.find_tables()
                for t in tabs.tables:
                    extracted = t.extract()
                    if extracted and len(extracted) > 1:
                        md_table = PDFParser._matrix_to_markdown(extracted)
                        page_tables.append(md_table)
            except Exception:
                pass
            tables_by_page[page_num] = page_tables

            # Extract embedded images
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_data = base_image["image"]
                    img_ext = base_image["ext"]
                    pil_img = Image.open(io.BytesIO(img_data))
                    # Only keep images that are large enough to be meaningful (ignore tiny icons/bullets)
                    if pil_img.width >= 100 and pil_img.height >= 100:
                        extracted_images.append({
                            "page": page_num,
                            "width": pil_img.width,
                            "height": pil_img.height,
                            "format": img_ext,
                            "pil_image": pil_img
                        })
                except Exception:
                    pass

        # Detect Language
        detected_language = "English"
        lower_text = all_text_combined.lower()
        spanish_markers = ["notificación", "reacción adversa", "fármaco", "paciente", "aemps", "hospital", "madrid", "gravedad"]
        german_markers = ["bericht", "unerwünschte", "arzneimittelwirkung", "charité", "patient", "berlin", "bfarm", "uaw"]
        
        spanish_hits = sum(1 for m in spanish_markers if m in lower_text)
        german_hits = sum(1 for m in german_markers if m in lower_text)
        
        if spanish_hits >= 3:
            detected_language = "Spanish"
        elif german_hits >= 3:
            detected_language = "German"

        # Detect Flavor
        flavor = "digital_form"
        if detected_language in ["Spanish", "German"]:
            flavor = "non_english"
        elif total_chars < 200 and page_count <= 3:
            flavor = "scanned_handwritten"
        elif any(k in lower_text for k in ["fda 3500a", "form 3500a", "cioms-i", "cioms i", "cioms form", "medwatch", "yellow card", "adverse reaction report", "defect report"]):
            flavor = "digital_form"
        elif any(k in lower_text for k in ["abstract", "references", "case series", "case report", "cohort", "journal", "doi:"]):
            flavor = "literature_article"

        return ParsedPDF(
            filename=filename,
            page_count=page_count,
            text_by_page=text_by_page,
            tables_by_page=tables_by_page,
            images=extracted_images,
            flavor=flavor,
            detected_language=detected_language,
            raw_doc=doc,
            blocks_by_page=blocks_by_page
        )

    @staticmethod
    def parse_pdf_file(file_path: Path) -> ParsedPDF:
        with open(file_path, "rb") as f:
            return PDFParser.parse_pdf_bytes(f.read(), filename=file_path.name)

    @staticmethod
    def _matrix_to_markdown(matrix: List[List[Any]]) -> str:
        clean_matrix = []
        for row in matrix:
            clean_row = [str(cell).replace("\n", " ").strip() if cell is not None else "" for cell in row]
            clean_matrix.append(clean_row)
        
        if not clean_matrix:
            return ""
        
        header = clean_matrix[0]
        col_count = len(header)
        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(["---"] * col_count) + " |"
        ]
        for r in clean_matrix[1:]:
            padded = r + [""] * (col_count - len(r))
            lines.append("| " + " | ".join(padded[:col_count]) + " |")
        return "\n".join(lines)
