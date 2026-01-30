import re

def clean_text(text):
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()

        # حذف خطوط خالی
        if not line:
            continue

        # حذف تگ‌های HTML مانند <!-- PageHeader -->
        if line.startswith("<!--") and line.endswith("-->"):
            continue

        # حذف شماره صفحات تنها شامل عدد
        if re.fullmatch(r"[0-9۰-۹]+", line):
            continue

        # حذف خطوط شامل PageHeader یا PageBreak
        if "PageHeader" in line or "PageBreak" in line or "PageNumber" in line:
            continue

        # حذف خطوط شامل IPS یا استاندارد ملی ایران (هدر)
        if re.match(r"^(IPS|استاندارد ملی ایران)", line):
            continue

        # حذف خطوط شامل آدرس، تلفن، ایمیل
        if "تلفن" in line or "دور نگار" in line or "پست الکترونیک" in line or "کدپستی" in line:
            continue

        # حذف خطوط کمیسیون تدوین
        if "کمیسیون" in line or "اعضا" in line or "ویرایش" in line:
            continue

        cleaned_lines.append(line)

    cleaned_text = "\n".join(cleaned_lines)
    return cleaned_text

with open("raw_raw_text.txt", "r", encoding="utf-8") as f:
    raw = f.read()

cleaned = clean_text(raw)

with open("cleaned_text.txt", "w", encoding="utf-8") as f:
    f.write(cleaned)

print ("Text cleaning completed. Cleaned text saved to 'cleaned_text.txt'.")

def fix_line_breaks(text):
    fixed = []

    for line in text.split("\n"):
        # اگر خط با نقطه یا دو نقطه یا علامت پایان جمله تمام نمی‌شود،
        # احتمالاً ادامه جمله است → به خط قبلی بچسبان
        if fixed and not re.search(r"[.!؟:]$", fixed[-1]):
            fixed[-1] += " " + line
        else:
            fixed.append(line)

    return "\n".join(fixed)


final_text = fix_line_breaks(cleaned)

with open("final_clean_text.txt", "w", encoding="utf-8") as f:
    f.write(final_text)

print ("final text saved to final_clean_text.txt")


def normalize_persian(text):
    # تبدیل کاف و یای عربی به فارسی
    text = text.replace("ي", "ی").replace("ك", "ک")

    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    trans_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(trans_table)

    # حذف فاصله‌های اضافی
    text = re.sub(r"\s+", " ", text)

    return text


normalized = normalize_persian(final_text)

with open("normalized_text.txt", "w", encoding="utf-8") as f:
    f.write(normalized)

print ("Normalized text saved to normalized_text.txt")