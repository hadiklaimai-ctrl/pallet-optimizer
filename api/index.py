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
            
            # שליפת הנתונים מה-UI
            raw_boxes = post_data.get('boxInputs', [])
            
            prompt = f"""
            Task: Professional 3D Palletizing Simulation.
            Pallet Dimensions: {pallet_l}x{pallet_w} cm.
            
            STRICT STACKING STRATEGY:
            1. TALL BOXES FIRST: Always start packing from the pallet base (Z=0) using the TALLEST boxes available in the inventory.
            2. VERTICAL HIERARCHY: Smaller/shorter boxes must only be placed AFTER the taller boxes have been positioned or when no more taller boxes can fit in a stable layer.
            3. STABLE LAYERS: Each layer (Z-range) must have a uniform height. Do not mix different box heights in the same horizontal layer unless it's the final top layer.
            
            GEOMETRY RULES:
            - Aim for 10 units per layer (120x100 cm) using: 2 rows of 3 (40x30) and 1 row of 4 (30x40 rotated).
            - Ensure every box has a "type" name and accurate "coords" in JSON.

            OUTPUT: Return ONLY a valid JSON object with an "items" array.
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
