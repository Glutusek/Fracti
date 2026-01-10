#!/usr/bin/env python3
import sys
import json
import pathlib
import os

# Try to auto-detect Windows Tesseract install and set pytesseract executable path
try:
    import pytesseract
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break
except Exception:
    # If pytesseract isn't installed yet or detection fails, ignore silently
    pass

# Ensure backend project root is on sys.path so local packages (e.g. `receipts`) import correctly
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from receipts.ocr_engine import OcrPipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_ocr.py path/to/image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    result = OcrPipeline(image_path).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
