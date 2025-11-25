import pypdf
import sys

def extract_text(pdf_path):
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        # Read first 5 pages to get the idea
        for page in reader.pages[:5]:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(extract_text("Interview prep GenAI Engineer.pdf"))
