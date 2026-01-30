import re
import json

# الگوی تشخیص بندها (پشتیبانی از فارسی و انگلیسی)
CLAUSE_PATTERN = re.compile(
    r"""
    ^\s*
    (
        [0-9۰-۹]+                # عدد اول
        (?:[-\.][0-9۰-۹]+)*      # ادامه مثل 3-1 یا 4.3.2
    )
    (?:\s+(.*))?                 # عنوان بند (اختیاری)
    $
    """,
    re.VERBOSE
)

def detect_clauses(text):
    lines = text.split("\n")
    clauses = []
    current_clause = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = CLAUSE_PATTERN.match(line)

        if match:
            # اگر بند جدید پیدا شد → بند قبلی را ذخیره کن
            if current_clause:
                clauses.append(current_clause)

            clause_id = match.group(1)
            title = match.group(2) if match.group(2) else ""

            current_clause = {
                "clause_id": clause_id,
                "title": title.strip(),
                "text": ""
            }

        else:
            # ادامه متن بند فعلی
            if current_clause:
                current_clause["text"] += line + " "

    # آخرین بند را هم اضافه کن
    if current_clause:
        clauses.append(current_clause)

    return clauses

# --- اجرای کد ---
# بجاي normalized_text.txt از cleaned_text.txt استفاده مي‌کنيم

with open("cleaned_text.txt", "r", encoding="utf-8") as f:
    cleaned_text = f.read()

clauses = detect_clauses(cleaned_text)

with open("clauses.json", "w", encoding="utf-8") as f:
    json.dump(clauses, f, ensure_ascii=False, indent=2)

print(" Clauses detected : ", len(clauses))