from pdfminer.high_level import extract_text
import tempfile

def extract_text_from_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    text = extract_text(tmp_path)
    return text
