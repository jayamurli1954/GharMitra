import sys
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import docx
import pandas as pd
import cv2

# Tell pytesseract where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def read_file(path):
    path = path.lower()

    if path.endswith(".pdf"):
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    if path.endswith(".png") or path.endswith(".jpg") or path.endswith(".jpeg"):
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="eng+hin+tam+tel+kan")

    if path.endswith(".docx"):
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)

    if path.endswith(".xlsx") or path.endswith(".xls"):
        df = pd.read_excel(path)
        return df.to_string()

    if path.endswith(".mp4"):
        cap = cv2.VideoCapture(path)
        success, frame = cap.read()
        if success:
            cv2.imwrite("frame.jpg", frame)
            return pytesseract.image_to_string(Image.open("frame.jpg"))
        return "No frames could be read from video."

    return "Unsupported file type."

if __name__ == "__main__":
    print(read_file(sys.argv[1]))
