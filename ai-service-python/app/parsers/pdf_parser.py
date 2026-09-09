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
        blocks_by_page: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        table_rows_by_page: Optional[Dict[int, List[Dict[str, Any]]]] = None
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
        self.table_rows_by_page = table_rows_by_page or {}

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
        table_rows_by_page: Dict[int, List[Dict[str, Any]]] = {}
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
            page_table_rows: List[Dict[str, Any]] = []
            try:
                tabs = page.find_tables()
                for table_idx, t in enumerate(tabs.tables):
                    extracted = t.extract()
                    if extracted and len(extracted) > 1:
                        md_table = PDFParser._matrix_to_markdown(extracted)
                        page_tables.append(md_table)
                        
                        # Process individual rows with their bboxes
                        headers = [str(c).replace("\n", " ").strip() if c is not None else "" for c in extracted[0]]
                        for row_idx, row in enumerate(extracted[1:], start=1):
                            row_cells = [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
                            # Try to get bbox from t.rows if available
                            row_bbox = None
                            try:
                                if hasattr(t, "rows") and row_idx < len(t.rows):
                                    r_obj = t.rows[row_idx]
                                    row_bbox = (float(r_obj.bbox[0]), float(r_obj.bbox[1]), float(r_obj.bbox[2]), float(r_obj.bbox[3]))
                            except Exception:
                                pass
                            if row_bbox is None:
                                row_bbox = (float(t.bbox[0]), float(t.bbox[1]), float(t.bbox[2]), float(t.bbox[3]))
                            
                            # Build readable key-value string
                            kv_pairs = []
                            for h, val in zip(headers, row_cells):
                                if h and val:
                                    kv_pairs.append(f"{h}: {val}")
                                elif val:
                                    kv_pairs.append(val)
                            row_text = " | ".join(kv_pairs) if kv_pairs else " ".join(row_cells)
                            
                            page_table_rows.append({
                                "page_number": page_num,
                                "table_no": table_idx,
                                "row_no": row_idx,
                                "headers": headers,
                                "values": row_cells,
                                "text": row_text,
                                "bbox": row_bbox
                            })
            except Exception:
                pass
            tables_by_page[page_num] = page_tables
            table_rows_by_page[page_num] = page_table_rows

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
                        rects = page.get_image_rects(xref)
                        bbox = None
                        if rects:
                            r = rects[0]
                            bbox = (float(r.x0), float(r.y0), float(r.x1), float(r.y1))
                        extracted_images.append({
                            "source_filename": filename,
                            "page": page_num,
                            "width": pil_img.width,
                            "height": pil_img.height,
                            "format": img_ext,
                            "pil_image": pil_img,
                            "bbox": bbox
                        })
                except Exception:
                    pass

        # Detect Language
        from app.parsers.language_detector import detect_language
        lower_text = all_text_combined.lower()
        detected_language = detect_language(all_text_combined)
        if detected_language == "Unknown":
            detected_language = "English" if total_chars >= 50 else "Unknown"

        # Detect Flavor
        flavor = "digital_form"
        if detected_language not in ("English", "Unknown"):
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
            blocks_by_page=blocks_by_page,
            table_rows_by_page=table_rows_by_page
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
