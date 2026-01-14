import os
import cv2
import json
import easyocr
import numpy as np
from receipt_ocr.processors import ReceiptProcessor
from receipt_ocr.providers import OpenAIProvider


class OcrPipeline:
    def __init__(self, image_path):
        self.image_path = image_path

        # Wczytujemy obraz tylko do odczytu wymiarów
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Nie można wczytać obrazu: {image_path}")
        self.height, self.width, _ = img.shape

        # --- KONFIGURACJA GEMINI ---
        # Pobieramy klucze, które ustawiłeś w .env
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            # Fallback lub błąd, jeśli zapomnisz o .env
            raise ValueError("Brak klucza API. Ustaw OPENAI_API_KEY w pliku .env")

        # Konfigurujemy providera, aby 'udawał' OpenAI, ale łączył się z Google
        self.provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        self.processor = ReceiptProcessor(self.provider)

        # --- KONFIGURACJA EASYOCR ---
        # Inicjalizujemy czytnik dla języka polskiego i angielskiego
        # gpu=False dla bezpieczeństwa (chyba że masz skonfigurowaną NVIDIA w Dockerze)
        self.reader = easyocr.Reader(['pl', 'en'], gpu=False)

    def run(self):
        """Główna metoda uruchamiana przez Celery"""

        # 1. MÓZG: Zapytaj Gemini co jest na paragonie
        print(f"--- [OCR] Wysyłanie do Gemini ({os.getenv('OPENAI_MODEL')})... ---")
        llm_items = self._get_llm_data()
        print(f"--- [OCR] Gemini znalazł {len(llm_items)} pozycji. ---")

        # 2. OCZY: Użyj EasyOCR do znalezienia gdzie jest tekst
        print("--- [OCR] Skanowanie pozycji (EasyOCR)... ---")
        raw_boxes = self._get_easyocr_boxes()

        # 3. SYNTEZA: Połącz wiedzę Gemini z ramkami EasyOCR
        final_items = []
        for item in llm_items:
            price = item.get("item_price", 0.0)
            name = item.get("item_name", "Nieznany")
            qty = item.get("item_quantity", 1)

            # Szukamy ramki pasującej do ceny
            box = self._find_box_by_price(price, raw_boxes)

            final_items.append({
                "name": name,
                "price": price,
                "quantity": qty,
                "box": box  # Jeśli None, frontend po prostu nie wyświetli ramki
            })

        return {
            "image_dim": {"width": self.width, "height": self.height},
            "items": final_items,
            "total_amount": sum(x['price'] for x in final_items)
        }

    def _get_llm_data(self):
        """Definiuje schemat JSON i wysyła zapytanie do modelu"""
        json_schema = {
            "type": "object",
            "properties": {
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string"},
                            "item_price": {"type": "number", "description": "Final total price..."},
                            "item_quantity": {"type": "number", "description": "Quantity of items detected"}
                        },
                        "required": ["item_name", "item_price", "item_quantity"]
                    }
                }
            },
            "required": ["line_items"]
        }

        try:
            # Wywołanie biblioteki receipt-ocr
            result = self.processor.process_receipt(
                self.image_path,
                json_schema=json_schema,
                model=os.getenv("OPENAI_MODEL", "gemini-2.5-flash-lite"),
                response_format_type="json_schema"
            )

            # Obsługa różnych typów odpowiedzi (string vs dict)
            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result

            return data.get("line_items", [])
        except Exception as e:
            print(f"--- [BŁĄD GEMINI] {e} ---")
            return []

    def _get_easyocr_boxes(self):
        """Zwraca surowe ramki wszystkich napisów na obrazku"""
        results = self.reader.readtext(self.image_path)
        boxes = []
        for (bbox, text, prob) in results:
            if prob > 0.3:  # Ignoruj bardzo niepewne odczyty
                (tl, tr, br, bl) = bbox
                # Konwersja formatu EasyOCR na x, y, w, h
                x = int(tl[0])
                y = int(tl[1])
                w = int(tr[0] - tl[0])
                h = int(bl[1] - tl[1])

                boxes.append({
                    "text": text,
                    "x": x, "y": y, "w": w, "h": h
                })
        return boxes

    def _find_box_by_price(self, price, raw_boxes):
        """Algorytm dopasowania ceny do ramki"""
        # Wzorce ceny: 12.99, 12,99, 12 (jeśli pełna liczba)
        price_patterns = [
            f"{price:.2f}",
            f"{price}".replace('.', ','),
        ]
        # Sama końcówka (grosze), np. "99" - często OCR widzi ją osobno
        minor_part = f"{price:.2f}".split('.')[1]

        best_box = None

        for box in raw_boxes:
            clean_text = box['text'].replace(' ', '').replace(',', '.').lower()

            # 1. Szukaj pełnej ceny
            if any(p in clean_text for p in price_patterns):
                best_box = box
                break

            # 2. Szukaj samych groszy (backup), jeśli tekst to cyfry i jest krótki
            if minor_part in clean_text and len(clean_text) < 5 and clean_text[0].isdigit():
                best_box = box
                # Nie przerywamy (break), szukamy dalej lepszego dopasowania

        if best_box:
            # Rozciągamy ramkę w lewo, aby objęła nazwę produktu
            return {
                "x": max(0, best_box['x'] - 450),  # Margines w lewo (dostosuj wg uznania)
                "y": best_box['y'] - 5,
                "w": best_box['w'] + 450,
                "h": best_box['h'] + 10
            }
        return None