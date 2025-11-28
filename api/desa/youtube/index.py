# api/desa/youtube/index.py
# TEST VERSION - Detaylı hata mesajları
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen
import json
import traceback

SHEET_ID = "1XJfW08gLJomg9ZYjJug_jDmhWs-eop3s0LOhEVo7VRA"
GID = "1208036518"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

class handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        try:
            # Sheet'e erişmeyi dene
            with urlopen(CSV_URL, timeout=10) as resp:
                status_code = resp.getcode()
                data = resp.read().decode("utf-8")
                
                # İlk 1000 karakteri göster
                preview = data[:1000] if len(data) > 1000 else data
                
                # Başarılı mesaj
                result = {
                    "status": "success",
                    "message": "Sheet erişilebilir!",
                    "http_status": status_code,
                    "data_length": len(data),
                    "first_lines": preview,
                    "sheet_url": CSV_URL,
                    "note": "Eğer bunu görüyorsanız, sheet public. Şimdi gerçek API'yi deploy edebilirsiniz."
                }
                
                body = json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
                self.send_response(200)
                
        except Exception as e:
            # Detaylı hata
            error = {
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "sheet_url": CSV_URL,
                "sheet_id": SHEET_ID,
                "gid": GID,
                "traceback": traceback.format_exc(),
                "fix": [
                    "1. Google Sheets'i açın: https://docs.google.com/spreadsheets/d/1XJfW08gLJomg9ZYjJug_jDmhWs-eop3s0LOhEVo7VRA/edit",
                    "2. File → Share → Publish to web",
                    "3. Entire Document → Comma-separated values (.csv) → Publish",
                    "4. Bu URL'yi tarayıcıda test edin: " + CSV_URL,
                    "5. Eğer CSV görüyorsanız, API'yi yeniden deploy edin"
                ]
            }
            
            body = json.dumps(error, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(500)
        
        self._set_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
