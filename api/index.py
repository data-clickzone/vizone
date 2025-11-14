from http.server import BaseHTTPRequestHandler
import urllib.request
import json

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
            
            # Parse CSV
            lines = csv_data.strip().split('\n')
            headers = lines[0].split(',')
            
            # Convert to JSON
            data = []
            for line in lines[1:]:
                values = line.split(',')
                if len(values) >= len(headers):
                    row = {}
                    for i, header in enumerate(headers):
                        try:
                            row[header.strip()] = values[i].strip()
                        except:
                            row[header.strip()] = ''
                    
                    # Calculate metrics
                    try:
                        impression = int(row.get('Impressions', 0) or 0)
                        click = int(row.get('Clicks', 0) or 0)
                        spend = float(row.get('Spend', 0) or 0)
                        revenue = float(row.get('Purchase Value', 0) or 0)
                        reach = int(row.get('Reach', 0) or 0)
                        purchase = int(row.get('Purchases (count)', 0) or 0)
                        
                        if impression > 0:
                            ctr = (click / impression) * 100
                            roas = revenue / spend if spend > 0 else 0
                            
                            data.append({
                                'name': row.get('Ad Name', ''),
                                'status': row.get('Status', ''),
                                'impression': impression,
                                'reach': reach,
                                'click': click,
                                'ctr': round(ctr, 2),
                                'spend': round(spend, 2),
                                'purchase': purchase,
                                'revenue': round(revenue, 2),
                                'roas': round(roas, 2),
                                'hasVideo': int(row.get('Video Plays (Any)', 0) or 0) > 0,
                                'imageUrl': row.get('Image URL', '')
                            })
                    except:
                        continue
            
            # Return JSON with CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
```

4. **Commit changes** tıklayın

---

## ✅ Şimdi Dosya Yapısı:
```
ivizone-api/
├── api/
│   └── index.py     ✅
├── vercel.json      ✅
└── README.md        ✅
