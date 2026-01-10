import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import re


class OcrPipeline:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Nie można wczytać obrazu: {image_path}")

        # Pobieramy oryginalne wymiary
        self.height, self.width, _ = self.image.shape

    def run(self):
        # 1. Preprocessing (Skalowanie + Binaryzacja)
        processed_img = self._preprocess()
        debug_path = self.image_path + "_debug.jpg"
        cv2.imwrite(debug_path, processed_img)
        print(f"--- [DEBUG OCR] Zapisano podgląd: {debug_path} ---")
        # 2. Ekstrakcja Danych
        ocr_data = self._extract_data(processed_img)

        # 3. Parsing (Wyciąganie produktów)
        return self._parse_data_with_coords(ocr_data)

    def _preprocess(self):
        # 1. Skalowanie (2x większy obraz - to zostawiamy, bo jest super)
        scaled = cv2.resize(self.image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 2. Skala szarości
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)

        # --- NOWOŚĆ 1: Lekkie rozmycie przed binaryzacją ---
        # To pomaga "zlać" kropki z drukarki igłowej w jedną całość
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Binaryzacja (Thresholding)

        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )

        kernel = np.ones((2, 2), np.uint8)

        binary = cv2.erode(binary, kernel, iterations=1)

        return binary

    def _extract_data(self, processed_image):

        custom_config = r'--oem 3 --psm 6 -l pol+eng'
        return pytesseract.image_to_data(
            processed_image,
            config=custom_config,
            output_type=Output.DICT
        )

    def _parse_data_with_coords(self, data):
        n_boxes = len(data['text'])
        lines_map = {}

        # Skalowanie powrotne współrzędnych

        SCALE_FACTOR = 2.0

        for i in range(n_boxes):
            if int(data['conf'][i]) > 30 and data['text'][i].strip():

                y_coord = int(data['top'][i]) // 20 * 20

                line_id = (data['block_num'][i], y_coord)

                if line_id not in lines_map:
                    lines_map[line_id] = []

                lines_map[line_id].append({
                    "text": data['text'][i],
                    "left": int(data['left'][i] / SCALE_FACTOR),
                    "top": int(data['top'][i] / SCALE_FACTOR),
                    "width": int(data['width'][i] / SCALE_FACTOR),
                    "height": int(data['height'][i] / SCALE_FACTOR)
                })

        parsed_items = []
        total_amount = 0.0


        price_pattern = re.compile(r'(\d+[.,]\d{2})')

        ignore_words = ['SUMA', 'RAZEM', 'PODATEK', 'VAT', 'PTU', 'SPRZEDAŻ', 'KARTA', 'RESZTA']

        for line_words in lines_map.values():
            # Sortujemy słowa po X (left), żeby tekst był po kolei
            line_words.sort(key=lambda x: x['left'])
            full_text = " ".join([w['text'] for w in line_words])


            # print(f"Analiza linii: '{full_text}'")

            # Filtrujemy nagłówki
            if any(ign in full_text.upper() for ign in ignore_words):
                continue

            matches = price_pattern.findall(full_text)
            if matches:

                price_str = matches[-1].replace(',', '.')

                try:
                    price = float(price_str)

                    # Nazwa to wszystko PRZED znalezioną ceną
                    # Musimy znaleźć indeks wystąpienia tej ceny w tekście
                    last_price_index = full_text.rfind(matches[-1])
                    name = full_text[:last_price_index].strip()

                    # Czyszczenie nazwy (usuwanie np. "1.000*" jeśli weszło w nazwę)
                    # Usuwamy "cyfra + gwiazdka" lub "cyfra + x"
                    name = re.sub(r'\d+[.,]?\d*\s*[x*]', '', name).strip()
                    name = re.sub(r'^\d+[\.\)\s]+', '', name)  # Usuń numerację na początku

                    if len(name) > 2 and price > 0:
                        # Obliczamy bounding box
                        min_x = min(w['left'] for w in line_words)
                        min_y = min(w['top'] for w in line_words)
                        max_x = max(w['left'] + w['width'] for w in line_words)
                        max_y = max(w['top'] + w['height'] for w in line_words)

                        parsed_items.append({
                            "name": name,
                            "price": price,
                            "quantity": 1,
                            "box": {
                                "x": min_x,
                                "y": min_y,
                                "w": max_x - min_x,
                                "h": max_y - min_y
                            }
                        })
                        total_amount += price
                except ValueError:
                    continue

        return {
            "image_dim": {"width": self.width, "height": self.height},
            "items": parsed_items,
            "total_amount": round(total_amount, 2),
        }