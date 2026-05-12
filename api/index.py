from http.server import BaseHTTPRequestHandler
import json
import os
import google.generativeai as genai

# הגדרת Gemini (המפתח נמשך מהכספת של Vercel)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# שימוש במודל Pro לדיוק מקסימלי בחישובים מרחביים
model = genai.GenerativeModel('gemini-1.5-pro') 

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            
            # פרומפט הנדסי מדויק למניעת ריחוף והבטחת 10 יחידות
            prompt = f"""
            Task: 3D Pallet Stacking Optimization.
            Pallet: 120x100.
            Boxes to pack: {post_data.get('boxes')}
            
            CRITICAL PHYSICS RULES:
            1. GRAVITY: Every box MUST sit on the floor (Z=0) or directly on top of another box. 
            2. NO FLOATING: A box's Z_min must equal the Z_max of the box below it.
            3. 10-UNIT LAYER PATTERN: For 40x30 boxes on a 120x100 pallet, use this exact layout:
               - Two rows of 3 boxes in 40x30 orientation (covers 120x60).
               - One row of 4 boxes rotated to 30x40 orientation (covers 120x40).
               - Total = 10 boxes per flat layer.
            
            OUTPUT:
            Return ONLY a JSON object with an "items" array. No conversational text.
            Format: {{"items": [{{"type": "string", "coords": {{"x": [min,max], "y": [min,max], "z": [min,max]}}}}]}}
            """
            
            response = model.generate_content(prompt)
            
            # ניקוי תגיות Markdown מהתשובה
            clean_res = response.text.strip().replace('```json', '').replace('```', '')
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(clean_res.encode())
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
