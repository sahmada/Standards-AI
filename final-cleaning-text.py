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