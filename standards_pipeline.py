import os
import re
import json
from typing import Dict, Any

from pdf2image import convert_from_path
import pytesseract

# اگر خواستی fallback متنی هم داشته باشی، این را فعال کن
USE_PYMUPDF_FALLBACK = False
try:
    import fitz  # PyMuPDF
except ImportError:
    USE_PYMUPDF_FALLBACK = False


# ============================
# تنظیمات عمومی
# ============================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Program Files\poppler-25.12.0\Library\bin"

INPUT_PDF_FOLDER = "./standards_pdf"
OUTPUT_TEXT_FOLDER = "./standards_text"
OUTPUT_JSON_FOLDER = "./standards_json"
METADATA_FILE = "./standards_metadata.json"


# ============================
# 1) OCR از PDF
# ============================

def ocr_pdf_to_text(pdf_path: str) -> str:
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
    full_text = ""
    for i, page in enumerate(pages):
        print(f"  [OCR] page {i+1}/{len(pages)} ...")
        text = pytesseract.image_to_string(page, lang="fas+eng")
        full_text += text + "\n"
    return full_text


# ============================
# 2) استخراج متن با PyMuPDF (اختیاری)
# ============================

def extract_text_pymupdf(pdf_path: str) -> str:
    if not USE_PYMUPDF_FALLBACK:
        return ""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"
    return full_text


# ============================
# 3) ارزیابی کیفیت متن
# ============================

def evaluate_text_quality(text: str) -> float:
    """
    یک معیار ساده: نسبت کاراکترهای الفبایی/عددی به کل کاراکترها.
    هرچه این نسبت بالاتر، متن تمیزتر.
    """
    if not text:
        return 0.0
    valid_chars = sum(ch.isalnum() for ch in text)
    total_chars = len(text)
    return valid_chars / total_chars


# ============================
# 4) پاک‌سازی متن
# ============================

def clean_text(text: str) -> str:
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("<!--") and line.endswith("-->"):
            continue
        if "PageHeader" in line or "PageBreak" in line or "PageNumber" in line:
            continue
        if re.fullmatch(r"[0-9۰-۹]+", line):
            continue
        if line.startswith("IPS") or line.startswith("استاندارد ملی ایران"):
            continue
        if "تلفن" in line or "دورن" in line or "پست الکترونیک" in line:
            continue
        if "کمیسیون" in line or "اعضا" in line or "ویرایش" in line:
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


# ============================
# 5) اصلاح شکستگی خطوط
# ============================

def fix_line_breaks(text: str) -> str:
    fixed = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        if fixed and not re.search(r"[.!؟:؛]$", fixed[-1]):
            fixed[-1] += " " + line
        else:
            fixed.append(line)

    return "\n".join(fixed)


# ============================
# 6) نرمال‌سازی فارسی
# ============================

def normalize_persian(text: str) -> str:
    text = text.replace("ي", "ی").replace("ك", "ک")
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(persian_digits, english_digits))
    text = re.sub(r"\s+", " ", text)
    return text


# ============================
# 7) تشخیص بندها
# ============================

CLAUSE_PATTERN = re.compile(
    r"""
    ^\s*
    (
        [0-9۰-۹]+
        (?:[-\.][0-9۰-۹]+)*
    )
    (?:\s+(.*))?
    $
    """,
    re.VERBOSE
)

def detect_clauses(text: str):
    lines = text.split("\n")
    clauses = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = CLAUSE_PATTERN.match(line)

        if match:
            if current:
                clauses.append(current)

            clause_id = match.group(1)
            title = match.group(2) if match.group(2) else ""

            current = {
                "clause_id": clause_id,
                "title": title.strip(),
                "text": ""
            }
        else:
            if current:
                current["text"] += line + " "

    if current:
        clauses.append(current)

    return clauses


# ============================
# 8) استخراج متادیتا از نام فایل
# ============================

def infer_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    اینجا ساده عمل می‌کنیم:
    - نوع استاندارد را از prefix می‌گیریم (IPS / ASME / API / ...)
    - بقیه را فعلاً به‌صورت خام نگه می‌داریم
    اگر بعداً خواستی، می‌توانی این را هوشمندتر کنی.
    """
    name = os.path.splitext(os.path.basename(filename))[0]

    if name.upper().startswith("IPS"):
        std_type = "IPS"
    elif name.upper().startswith("ASME"):
        std_type = "ASME"
    elif name.upper().startswith("API"):
        std_type = "API"
    else:
        std_type = "UNKNOWN"

    return {
        "standard_code": name,
        "standard_type": std_type,
        "version": None,      # اگر خواستی بعداً از نام فایل استخراج کن
        "discipline": None,   # بعداً می‌توانی دستی یا خودکار پر کنی
        "language": "fa"      # فرض اولیه؛ اگر لازم شد تشخیص زبان اضافه کن
    }


# ============================
# 9) پردازش یک PDF کامل
# ============================

def process_single_pdf(pdf_path: str,
                       text_folder: str,
                       json_folder: str) -> Dict[str, Any]:
    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]

    print(f"\n=== Processing PDF: {filename} ===")

    # 1) OCR
    ocr_text = ocr_pdf_to_text(pdf_path)
    ocr_quality = evaluate_text_quality(ocr_text)
    print(f"  OCR quality: {ocr_quality:.3f}")

    final_text = ocr_text
    final_source = "ocr"

    # 2) (اختیاری) fallback به PyMuPDF اگر OCR خیلی بد بود
    if USE_PYMUPDF_FALLBACK and ocr_quality < 0.4:
        print("  OCR quality is low, trying PyMuPDF...")
        text_pm = extract_text_pymupdf(pdf_path)
        pm_quality = evaluate_text_quality(text_pm)
        print(f"  PyMuPDF quality: {pm_quality:.3f}")

        if pm_quality > ocr_quality:
            print("  Using PyMuPDF text instead of OCR.")
            final_text = text_pm
            final_source = "pymupdf"

    # 3) ذخیره متن خام
    os.makedirs(text_folder, exist_ok=True)
    text_path = os.path.join(text_folder, base_name + ".txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"  Saved raw text → {text_path}")

    # 4) پاک‌سازی + نرمال‌سازی + بندها
    cleaned = clean_text(final_text)
    fixed = fix_line_breaks(cleaned)
    normalized = normalize_persian(fixed)
    #clauses = detect_clauses(normalized)
    clauses = detect_clauses(fixed)

    # 5) افزودن متادیتا به هر بند
    meta = infer_metadata_from_filename(filename)
    for c in clauses:
        c["standard"] = meta["standard_code"]

    # 6) ذخیره JSON بندها
    os.makedirs(json_folder, exist_ok=True)
    json_path = os.path.join(json_folder, base_name + ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(clauses, f, ensure_ascii=False, indent=2)
    print(f"  Saved clauses JSON → {json_path}  ({len(clauses)} clauses)")

    # 7) متادیتای سطح استاندارد
    meta_record = {
        **meta,
        "file_pdf": os.path.abspath(pdf_path),
        "file_text": os.path.abspath(text_path),
        "file_json": os.path.abspath(json_path),
        "num_clauses": len(clauses),
        "text_source": final_source,
        "ocr_quality": ocr_quality
    }

    return meta_record


# ============================
# 10) پردازش همهٔ PDFها + ساخت متادیتای مرکزی + فایل جامع بندها
# ============================

def process_all_pdfs(pdf_folder: str,
                     text_folder: str,
                     json_folder: str,
                     metadata_file: str,
                     make_global_json: bool = True):
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(text_folder, exist_ok=True)
    os.makedirs(json_folder, exist_ok=True)

    all_metadata = []
    all_clauses = []

    for file in os.listdir(pdf_folder):
        if not file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(pdf_folder, file)
        meta = process_single_pdf(pdf_path, text_folder, json_folder)
        all_metadata.append(meta)

        # خواندن JSON همین استاندارد برای ساخت فایل جامع
        if make_global_json:
            with open(meta["file_json"], "r", encoding="utf-8") as f:
                clauses = json.load(f)
            all_clauses.extend(clauses)

    # ذخیره متادیتای مرکزی
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)
    print(f"\nSaved metadata → {metadata_file}")

    # ذخیره فایل جامع بندها
    if make_global_json:
        global_json_path = os.path.join(os.path.dirname(metadata_file), "all_clauses.json")
        with open(global_json_path, "w", encoding="utf-8") as f:
            json.dump(all_clauses, f, ensure_ascii=False, indent=2)
        print(f"Saved global clauses JSON → {global_json_path}")
        print("Total clauses:", len(all_clauses))


# ============================
# اجرای اصلی
# ============================

if __name__ == "__main__":
    process_all_pdfs(
        pdf_folder=INPUT_PDF_FOLDER,
        text_folder=OUTPUT_TEXT_FOLDER,
        json_folder=OUTPUT_JSON_FOLDER,
        metadata_file=METADATA_FILE,
        make_global_json=True
    )