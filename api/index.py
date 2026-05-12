from http.server import BaseHTTPRequestHandler
import json
import os
import google.generativeai as genai

# הגדרת Gemini (המפתח נמשך מהכספת של Vercel)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash') 

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        
        # הפרומפט שיגרום ל-Gemini "לחשוב" על קומבינציות
        prompt = f"""
        CONTEXT: 3D Pallet Stacking Optimization.
        PALLET: {post_data.get('pallet')}
        BOXES: {post_data.get('boxes')}
        
        CRITICAL GOAL: Maximize space utilization. 
        Note: For 40x30 boxes on a 120x100 pallet, you MUST find a way to fit 10 units per layer by rotating some boxes (e.g., 6 boxes at 40x30 and 4 boxes at 30x40).
        
        REQUIRED OUTPUT:
        A JSON object with a key "items" containing an array of:
        {{"type": "name", "coords": {{"x": [min,max], "y": [min,max], "z": [min,max]}}}}
        
        Return ONLY valid JSON. No conversational text.
        """
        
        try:
            response = model.generate_content(prompt)
            # ניקוי פורמט ה-Markdown שה-LLM לפעמים מוסיף
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
