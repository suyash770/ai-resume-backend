import fitz  # PyMuPDF

def extract_text_from_pdf(file):
    try:
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.lower()
    except:
        return ""
