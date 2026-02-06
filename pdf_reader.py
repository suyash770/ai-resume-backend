import fitz  # PyMuPDF

def extract_text_from_pdf(file):
    try:
        # Crucial fix: Reset the file pointer to the start of the stream
        file.seek(0)
        file_content = file.read()
        
        text = ""
        with fitz.open(stream=file_content, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text.lower().strip()
    except Exception as e:
        print(f"Extraction Error: {e}")
        return ""