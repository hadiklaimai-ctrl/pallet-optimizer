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
            
            prompt = f"""
            Task: 3D Palletizing Simulation.
            Pallet Size: {pallet_l}x{pallet_w} cm.
            Inventory: 20 Small Boxes (40x30x4 cm), 15 Large Boxes (40x30x8 cm).

            STRICT STACKING ORDER (Total Height: 24cm):
            1. LAYER 1 (Bottom - Z: 0-8cm): 
               - Sub-layer L1.1 (Z: 0-4): 10 Small Boxes.
               - Sub-layer L1.2 (Z: 4-8): 10 Small Boxes (Placed exactly on top of L1.1).
            2. LAYER 2 (Middle - Z: 8-16cm):
               - 10 Large Boxes (40x30x8 cm).
            3. LAYER 3 (Top - Z: 16-24cm):
               - 5 Large Boxes (40x30x8 cm).

            GEOMETRY RULES:
            - Each layer of 10 boxes must be arranged as: 2 rows of 3 boxes (40x30) + 1 row of 4 boxes (30x40 rotated).
            - Total surface utilization for 10 boxes must be 120x100 cm.
            - Ensure every box has a "type" ("Small" or "Large") and correct "coords".

            OUTPUT: Return ONLY a JSON object with an "items" array.
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
