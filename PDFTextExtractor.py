import fitz  # PyMuPDF
import io
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

class PDFTextExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.text = ""

    def extract_text(self):
        """Extracts selectable text, OCRs embedded images, and full-page images if needed."""
        try:
            with fitz.open(self.file_path) as doc:
                all_text = []

                for page_number, page in enumerate(doc):
                    # 1. Extract selectable text
                    page_text = page.get_text()
                    if page_text.strip():
                        all_text.append(page_text)
                    else:
                        # 2. Fallback: Full-page image OCR (for scanned PDFs)
                        pix = page.get_pixmap(dpi=300)
                        image = Image.open(io.BytesIO(pix.tobytes()))
                        ocr_result = pytesseract.image_to_string(image, lang='eng')
                        all_text.append(ocr_result)

                    # 3. OCR on embedded images (if any)
                    for img_index, img in enumerate(page.get_images(full=True)):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image = Image.open(io.BytesIO(image_bytes))
                        ocr_result = pytesseract.image_to_string(image, lang='eng')
                        all_text.append(ocr_result)

                self.text = "".join(all_text)
        except Exception as e:
            print(f"Error reading PDF with OCR: {e}")
        return self.text

# Example usage
extractor = PDFTextExtractor("test_files/scanned.pdf")
text = extractor.extract_text()
print(text)

extractor = PDFTextExtractor("test_files/text_with_img.pdf")
text = extractor.extract_text()
print(text)

extractor = PDFTextExtractor("test_files/example.pdf")
text = extractor.extract_text()
print(text)