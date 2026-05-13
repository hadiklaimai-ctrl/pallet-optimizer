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
            pallet_l = 120
            pallet_w = 100
            
            prompt = f"""
            Task: 3D Palletizing Optimization.
            Inventory: 15 Large Boxes (40x30x8 cm), 20 Small Boxes (40x30x4 cm).
            Pallet: 120x100 cm.

            STRICT LAYER BLUEPRINT (Total Height: 20cm):
            
            1. LAYER 1 (Z: 0-8cm): 
               - Place 10 Large Boxes (5K) to cover the full 120x100 surface.
            
            2. LAYER 2 (Z: 8-16cm) - COMPOSITE LAYER:
               - Section A: Place the remaining 5 Large Boxes (5K).
               - Section B: In the remaining space, place 5 Small Boxes (5K ei) at Z: 8-12.
               - Section C: Place another 5 Small Boxes (5K ei) DIRECTLY ON TOP of the ones in Section B (Z: 12-16).
               - Result: The entire Layer 2 must end at exactly Z=16cm.
            
            3. LAYER 3 (Z: 16-20cm):
               - Place the remaining 10 Small Boxes (5K ei).

            GEOMETRY:
            - Each full layer of 10 units must use the 120x100 layout (6 boxes at 40x30 + 4 boxes at 30x40).
            - Use "type": "5K" for Large and "5K ei" for Small.

            OUTPUT: JSON with "items" array only.
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
