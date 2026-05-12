from http.server import BaseHTTPRequestHandler
import json
import os
from google import genai

# אתחול הלקוח - וודא שהמפתח GEMINI_API_KEY קיים ב-Vercel Settings
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            post_data = json.loads(body)
            
            prompt = f"""
            Task: Professional 3D Pallet Stacking.
            Pallet: 120x100.
            Boxes: {post_data.get('boxes')}
            
            STRICT RULES:
            - Every layer MUST have 10 boxes (6 boxes at 40x30 + 4 boxes at 30x40).
            - NO floating boxes. Every box must sit on Z=0 or on another box.
            - Output ONLY JSON with an "items" array.
            """

            # שימוש ב-Pro לדיוק מקסימלי
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents=prompt
            )
            
            # ניקוי בטוח של התשובה
            text_res = response.text
            if "```json" in text_res:
                text_res = text_res.split("```json")[1].split("```")[0]
            elif "```" in text_res:
                text_res = text_res.split("```")[1].split("```")[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(text_res.strip().encode())

        except Exception as e:
            # אם יש שגיאה, נחזיר אותה בצורה מסודרת ללוגים
            print(f"Error occurred: {str(e)}")
            self.send_response(200) # נחזיר 200 כדי ש-Base44 לא יקרוס, אבל עם הודעת שגיאה
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "fallback": True}).encode())
