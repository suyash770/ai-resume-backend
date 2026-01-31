from PyPDF2 import PdfReader
import io

def extract_text_from_pdf(file):
    # Convert file to binary stream
    pdf_stream = io.BytesIO(file.read())
    reader = PdfReader(pdf_stream)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return text
