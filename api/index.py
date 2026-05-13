from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            post_data = json.loads(body)
            pallet = post_data.get('pallet', {})
            pallet_l = pallet.get('length_cm', 120)
            pallet_w = pallet.get('width_cm', 100)
            
            raw_boxes = post_data.get('boxInputs', [])
            boxes_info = ""
            for b in raw_boxes:
                m = b.get('material', {})
                boxes_info += f"- {b.get('qty')} units of '{m.get('packaging_name')}': {m.get('length_cm')}x{m.get('width_cm')}x{m.get('height_cm')} cm\n"

            prompt = f"""
            Act as a Professional Logistics Optimization Engine.
            Task: Pack a {pallet_l}x{pallet_w} cm pallet.
            
            INVENTORY:
            {boxes_info}

            STRICT STABILITY RULES:
            1. UNIFORM LAYER HEIGHT: Every box within a single layer (the same Z-range) MUST have the exact same height. 
            2. FLAT SURFACE: You are forbidden from mixing different heights in an intermediate layer. Each layer must provide a perfectly flat surface for the next one.
            3. EXCEPTION: Only the very last (top-most) layer of the pallet may contain boxes of different heights.
            4. COORDINATES: Pallet starts at (0,0,0). Max boundaries are {pallet_l}x{pallet_w}.

            STRATEGY:
            - Maximize surface utilization using rotations (90 deg).
            - Group boxes of the same height together to form full, level layers.

            OUTPUT: 
            Return ONLY a JSON object with an "items" array. 
            Format: {{ "type": "Box Name", "coords": {{ "x": [s, e], "y": [s, e], "z": [s, e] }} }}
            """

            response = client.models.generate_content(model='gemini-1.5-pro', contents=prompt)
            clean_res = response.text.strip().replace('```json', '').replace('```', '')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(clean_res.encode())

        except Exception as e:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
