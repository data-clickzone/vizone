from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import csv
from io import StringIO

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Google Sheets CSV export URL
            SHEET_ID = '1a83PZ04MfUmXj56Xxruulao1nqf6grBx_Yy9LRKlH4M'
            GID = '676609355'
            url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'
            
            # Fetch CSV data
            with urllib.request.urlopen(url) as response:
                csv_data = response.read().decode('utf-8')
            
            # Parse CSV properly using csv module
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            
            # Convert to JSON
            data = []
            for row in reader:
                try:
                    # Get values with defaults
                    impression = int(row.get('Impressions', '0') or 0)
                    click = int(row.get('Clicks', '0') or 0)
                    spend = float(row.get('Spend', '0') or 0)
                    revenue = float(row.get('Purchase Value', '0') or 0)
                    reach = int(row.get('Reach', '0') or 0)
                    purchase = int(row.get('Purchases (count)', '0') or 0)
                    video_plays = int(row.get('Video Plays (Any)', '0') or 0)
                    
                    # Only include rows with impressions
                    if impression > 0:
                        ctr = (click / impression) * 100 if impression > 0 else 0
                        roas = revenue / spend if spend > 0 else 0
                        
                        data.append({
                            'name': row.get('Ad Name', '').strip(),
                            'status': row.get('Status', '').strip(),
                            'impression': impression,
                            'reach': reach,
                            'click': click,
                            'ctr': round(ctr, 2),
                            'spend': round(spend, 2),
                            'purchase': purchase,
                            'revenue': round(revenue, 2),
                            'roas': round(roas, 2),
                            'hasVideo': video_plays > 0,
                            'imageUrl': row.get('Image URL', '').strip()
                        })
                except (ValueError, KeyError, ZeroDivisionError) as e:
                    # Skip rows with errors
                    continue
            
            # Return JSON with CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            # Return error
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'error': str(e),
                'type': type(e).__name__
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
