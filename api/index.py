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
            Act as a High-End Industrial Pallet Optimizer.
            
            INVENTORY TO PACK:
            {boxes_info}

            PRIMARY GOAL: MINIMIZE TOTAL PALLET HEIGHT (Max Z-value).
            
            STRICT PACKING RULES:
            1. COMPOSITE LAYERING: You can mix boxes of different heights in the same layer IF they stack to reach the same height. 
               Example: If Box A is 8cm and Box B is 4cm, you can stack two Box B units (4+4=8) next to one Box A unit to maintain a perfectly flat ceiling for that layer.
            2. SURFACE MAXIMIZATION: Every layer should aim for 100% surface coverage of the {pallet_l}x{pallet_w} pallet before starting a new layer height.
            3. STABILITY: Every box must have full support from underneath. No overlapping or floating.
            4. UNIFORM CEILING: Every intermediate layer MUST provide a flat, uniform surface for the next layer. 

            STRATEGY HINT: To get to 20cm height for 15 large (8cm) and 20 small (4cm) boxes:
            - Layer 1 (Z 0-8): 10 large boxes.
            - Layer 2 (Z 8-16): 5 large boxes + 10 small boxes (stacked in 5 pairs of 2).
            - Layer 3 (Z 16-20): Remaining 10 small boxes.
            Total Height = 20cm.

            OUTPUT: Return ONLY a JSON object with an "items" array.
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
