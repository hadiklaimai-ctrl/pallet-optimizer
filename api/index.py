from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai

# הגדרת הלקוח של Gemini
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            post_data = json.loads(body)
            
            # חילוץ נתוני המשטח והקרטונים מה-Request
            pallet = post_data.get('pallet', {})
            pallet_l = pallet.get('length_cm', 120)
            pallet_w = pallet.get('width_cm', 100)
            pallet_h = pallet.get('max_height_cm', 200)
            
            raw_boxes = post_data.get('boxInputs', [])
            box_descriptions = []
            for b in raw_boxes:
                m = b.get('material', {})
                qty = b.get('qty', 0)
                desc = f"{qty} units of '{m.get('packaging_name')}' (Dims: {m.get('length_cm')}x{m.get('width_cm')}x{m.get('height_cm')} cm)"
                box_descriptions.append(desc)
            
            box_info_str = "\n".join(box_descriptions)

            # Prompt אופטימיזציה מתקדם
            prompt = f"""
            Role: Expert Logistics & Spatial Optimization Engine.
            Task: Pack a pallet ({pallet_l}x{pallet_w} cm, max height {pallet_h} cm) with the following boxes:
            {box_info_str}

            GOAL: Maximize volume utilization (Aim for 100%). 
            
            RULES:
            1. Use the EXACT dimensions provided for each box type.
            2. You MAY rotate boxes (e.g., change 40x30 to 30x40) to fit more units.
            3. Boxes must stay within pallet boundaries ({pallet_l}x{pallet_w}).
            4. Stack boxes in logical layers (Z-axis).
            5. Ensure stability: boxes should be placed on the pallet or on top of other boxes.

            OUTPUT: Return ONLY a valid JSON object with an "items" array.
            Each item format: 
            {{ "type": "Box Name", "coords": {{ "x": [start, end], "y": [start, end], "z": [start, end] }} }}
            """

            # יצירת הפתרון באמצעות Gemini
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents=prompt
            )
            
            # ניקוי התשובה מסימני Markdown אם קיימים
            clean_res = response.text.strip().replace('```json', '').replace('```', '')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(clean_res.encode())

        except Exception as e:
            self.send_response(200) # מחזירים 200 כדי ש-Base44 יוכל לקרוא את השגיאה
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
