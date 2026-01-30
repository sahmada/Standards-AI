import os
import re
import json
from pdf2image import convert_from_path
import pytesseract


# ============================================================
# تنظیم مسیر Tesseract (اگر PATH مشکل داشت)
# ============================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path=r"C:\Program Files\poppler-25.12.0\Library\bin"

# ============================================================
# 1) استخراج متن از PDF با OCR (Tesseract)
# ============================================================

def extract_pdf_text_ocr(pdf_path, poppler_path=poppler_path):
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)
    full_text = ""

    for i, page in enumerate(pages):
        print(f"  OCR page {i+1}/{len(pages)} ...")
        text = pytesseract.image_to_string(page, lang="fas+eng")
        full_text += text + "\n"

    return full_text


# ============================================================
# 2) پاک‌سازی متن
# ============================================================

def clean_text(text):
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


# ============================================================
# 3) اصلاح شکستگی خطوط
# ============================================================

def fix_line_breaks(text):
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


# ============================================================
# 4) نرمال‌سازی فارسی
# ============================================================

def normalize_persian(text):
    text = text.replace("ي", "ی").replace("ك", "ک")
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    text = text.translate(str.maketrans(persian_digits, english_digits))
    text = re.sub(r"\s+", " ", text)
    return text


# ============================================================
# 5) تشخیص بندها (Clause Detection)
# ============================================================

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

def detect_clauses(text):
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


# ============================================================
# 6) پردازش یک PDF → JSON مستقل
# ============================================================

def process_single_pdf(pdf_path, output_folder):
    filename = os.path.basename(pdf_path)
    standard_name = filename.replace(".pdf", "")

    print(f"\nProcessing: {standard_name}")

    raw = extract_pdf_text_ocr(pdf_path)
    cleaned = clean_text(raw)
    fixed = fix_line_breaks(cleaned)
    normalized = normalize_persian(fixed)
    #clauses = detect_clauses(normalized)
    clauses = detect_clauses(cleaned)

    for c in clauses:
        c["standard"] = standard_name

    out_path = os.path.join(output_folder, f"{standard_name}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clauses, f, ensure_ascii=False, indent=2)

    print(f"Saved: {out_path}  ({len(clauses)} clauses)")

    return clauses


# ============================================================
# 7) پردازش همهٔ PDFها + ساخت فایل جامع
# ============================================================

def process_all_pdfs(input_folder, output_folder, make_global_json=True):
    all_clauses = []

    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            clauses = process_single_pdf(pdf_path, output_folder)
            all_clauses.extend(clauses)

    if make_global_json:
        global_path = os.path.join(output_folder, "all_clauses.json")
        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(all_clauses, f, ensure_ascii=False, indent=2)
        print(f"\nGlobal JSON saved: {global_path}  (Total clauses: {len(all_clauses)})")

    return all_clauses


# ============================================================
# اجرای اصلی
# ============================================================

if __name__ == "__main__":
    input_folder = "./standards"
    output_folder = "./output"

    os.makedirs(output_folder, exist_ok=True)

    process_all_pdfs(input_folder, output_folder, make_global_json=True)