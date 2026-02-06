import fitz

def extract_text_from_pdf(file):
    try:
        file.seek(0)
        file_content = file.read()
        text = ""
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.lower().strip()
    except Exception as e:
        print(f"Error: {e}")
        return ""