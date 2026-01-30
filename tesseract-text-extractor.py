import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from pdf2image import convert_from_path

pages = convert_from_path(r".\standards\IPS-E-PR-850(2).pdf", dpi=300)

text = ""
for p in pages:
    text += pytesseract.image_to_string(p, lang="fas+eng") + "\n"

with open("tesseract_ocr_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print("OCR text extraction complete. Check 'tesseract_ocr_text.txt' for the output.")