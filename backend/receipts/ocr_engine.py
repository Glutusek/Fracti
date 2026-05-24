import os
import cv2
import json
from receipt_ocr.processors import ReceiptProcessor
from receipt_ocr.providers import OpenAIProvider


class OcrPipeline:
    def __init__(self, image_path):
        self.image_path = image_path

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Nie można wczytać obrazu: {image_path}")
        self.height, self.width, _ = img.shape

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise ValueError("Brak klucza API. Ustaw OPENAI_API_KEY w pliku .env")

        self.provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        self.processor = ReceiptProcessor(self.provider)

    def run(self):
        print(f"--- [OCR] Wysyłanie do Gemini ({os.getenv('OPENAI_MODEL')})... ---")
        llm_items = self._get_llm_data()
        print(f"--- [OCR] Gemini znalazł {len(llm_items)} pozycji. ---")

        final_items = []
        for item in llm_items:
            price = item.get("item_price", 0.0)
            name = item.get("item_name", "Nieznany")
            qty = item.get("item_quantity", 1)

            final_items.append({
                "name": name,
                "price": price,
                "quantity": qty,
                "box": None
            })

        return {
            "image_dim": {"width": self.width, "height": self.height},
            "items": final_items,
            "total_amount": sum(x['price'] for x in final_items)
        }

    def _get_llm_data(self):
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
            result = self.processor.process_receipt(
                self.image_path,
                json_schema=json_schema,
                model=os.getenv("OPENAI_MODEL", "gemini-2.5-flash-lite"),
                response_format_type="json_schema"
            )

            if isinstance(result, str):
                data = json.loads(result)
            else:
                data = result

            return data.get("line_items", [])
        except Exception as e:
            print(f"--- [BŁĄD GEMINI] {e} ---")
            return []

    def _find_box_by_price(self, price, raw_boxes):
        price_patterns = [
            f"{price:.2f}",
            f"{price}".replace('.', ','),
        ]
        minor_part = f"{price:.2f}".split('.')[1]

        best_box = None

        for box in raw_boxes:
            clean_text = box['text'].replace(' ', '').replace(',', '.').lower()

            if any(p in clean_text for p in price_patterns):
                best_box = box
                break

            if minor_part in clean_text and len(clean_text) < 5 and clean_text[0].isdigit():
                best_box = box

        if best_box:
            return {
                "x": max(0, best_box['x'] - 450),
                "y": best_box['y'] - 5,
                "w": best_box['w'] + 450,
                "h": best_box['h'] + 10
            }
        return None