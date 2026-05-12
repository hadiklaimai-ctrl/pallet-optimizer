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
            
            # שלב ה"מתרגם": חילוץ נתונים מהמבנה של Base44 שראינו
            raw_boxes = post_data.get('boxInputs', [])
            formatted_boxes = []
            for b in raw_boxes:
                m = b.get('material', {})
                qty = b.get('qty', 0)
                dims = f"{m.get('length_cm')}x{m.get('width_cm')}x{m.get('height_cm')}"
                formatted_boxes.append(f"{qty} boxes of {dims}")
            
            box_desc = ", ".join(formatted_boxes)
            
            prompt = f"""
            Task: Pallet Optimization (120x100 pallet).
            Boxes to pack: {box_desc}
            
            STRICT RULES:
            - Every layer MUST have exactly 10 boxes (6 boxes at 40x30 + 4 boxes at 30x40).
            - Total boxes to arrange: 30.
            - Output ONLY JSON with an "items" array. No text.
            """

            response = client.models.generate_content(model='gemini-1.5-pro', contents=prompt)
            text_res = response.text.strip().replace('```json', '').replace('```', '')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(text_res.encode())

        except Exception as e:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
