import fitz  # PyMuPDF

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        text = page.get_text("text")
        full_text += text + "\n"

    return full_text


raw_text = extract_pdf_text(r".\standards\IPS-E-PR-850(2).pdf")

with open("PyMuPDF_raw_text.txt", "w", encoding="utf-8") as f:
    f.write(raw_text)

print("Text extraction complete. Check 'PyMuPDF_raw_text.txt' for the output.")