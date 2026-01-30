import pdfplumber

def extract_with_pdfplumber(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

raw_text = extract_with_pdfplumber(r".\standards\IPS-E-PR-850(2).pdf")

with open("plumber_raw.txt", "w", encoding="utf-8") as f:
    f.write(raw_text)
print("Text extraction complete. Check 'plumber_raw.txt' for the output.")