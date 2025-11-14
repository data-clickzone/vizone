from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import csv
from collections import defaultdict

# Google Sheets ayarları
SHEET_KEY = "2PACX-1vS0TLi3H4e3gTxh8ZfOqiwKqCIZ2Yp7VZ5_YKn2TO2exNDRKWC8HO9KcAZ0YJHzxugIjoiEfSDUoN0W"
GID = "676609355"  # Meta_Pivot_AdName_Weekly sekme ID'si

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        try:
            # Google Sheets CSV export URL (published sheets için)
            url = f"https://docs.google.com/spreadsheets/d/e/{SHEET_KEY}/pub?gid={GID}&single=true&output=csv"
            
            # CSV verisini çek
            with urllib.request.urlopen(url) as response:
                csv_data = response.read().decode('utf-8')
            
            # CSV'yi parse et
            lines = csv_data.strip().split('\n')
            reader = csv.reader(lines)
            rows = list(reader)
            
            if len(rows) < 2:
                self.send_error(500, "Sheet boş veya hatalı format")
                return
            
            # Parse ve grupla
            assets = self.parse_sheet_data(rows)
            
            # JSON yanıt gönder
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = json.dumps(assets, ensure_ascii=False)
            self.wfile.write(response_data.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'error': str(e),
                'message': 'Veri çekme hatası'
            })
            self.wfile.write(error_response.encode('utf-8'))
    
    def parse_sheet_data(self, rows):
        """
        Google Sheets'teki Meta_Pivot_AdName_Weekly formatını parse eder
        
        Format:
        Row 0: Headers (Metric, Ad Name, Date1, Date2, ..., Total)
        Row 1+: Data (Tıklama, AdName1, val1, val2, ...)
        """
        
        # Header'ları al
        headers = rows[0]
        
        # Ad Name ve tarih sütunlarını bul
        ad_name_idx = None
        image_url_idx = None
        date_columns = []
        
        for idx, header in enumerate(headers):
            header_lower = header.lower().strip()
            if 'ad name' in header_lower or header_lower == 'name':
                ad_name_idx = idx
            elif 'image' in header_lower or 'url' in header_lower:
                image_url_idx = idx
            elif idx >= 2 and header and 'total' not in header_lower:
                # 2. sütundan sonraki tarihli sütunlar
                date_columns.append({
                    'index': idx,
                    'date': header.strip()
                })
        
        if ad_name_idx is None:
            raise ValueError("Ad Name sütunu bulunamadı!")
        
        # Verileri grupla (Ad Name bazında)
        grouped_data = defaultdict(lambda: {
            'name': '',
            'imageUrl': '',
            'status': 'ACTIVE',
            'weeklyData': {
                'weeks': [col['date'] for col in date_columns],
                'impressions': [],
                'clicks': [],
                'ctr': [],
                'cpc': [],
                'spend': [],
                'purchases': [],
                'revenue': [],
                'roas': []
            }
        })
        
        # Her satırı işle
        for row in rows[1:]:
            if len(row) < 3:
                continue
            
            metric_name = row[0].strip()
            ad_name = row[ad_name_idx].strip() if ad_name_idx < len(row) else ''
            
            if not ad_name or not metric_name:
                continue
            
            # İlk defa görülen ad ise bilgileri kaydet
            if not grouped_data[ad_name]['name']:
                grouped_data[ad_name]['name'] = ad_name
                if image_url_idx and image_url_idx < len(row):
                    grouped_data[ad_name]['imageUrl'] = row[image_url_idx].strip()
            
            # Haftalık değerleri çek
            weekly_values = []
            for date_col in date_columns:
                if date_col['index'] < len(row):
                    value = row[date_col['index']].strip()
                    # Temizle: ₺, %, virgül vs.
                    value = value.replace('₺', '').replace('%', '').replace(',', '').strip()
                    try:
                        weekly_values.append(float(value) if value else 0)
                    except ValueError:
                        weekly_values.append(0)
                else:
                    weekly_values.append(0)
            
            # Metriğe göre doğru diziye ekle
            metric_lower = metric_name.lower()
            
            if 'impression' in metric_lower or 'gösterim' in metric_lower:
                grouped_data[ad_name]['weeklyData']['impressions'] = weekly_values
            elif 'tıklama' in metric_lower or 'click' in metric_lower:
                grouped_data[ad_name]['weeklyData']['clicks'] = weekly_values
            elif metric_lower == 'ctr':
                grouped_data[ad_name]['weeklyData']['ctr'] = weekly_values
            elif metric_lower == 'cpc':
                grouped_data[ad_name]['weeklyData']['cpc'] = weekly_values
            elif 'satış' in metric_lower or 'purchase' in metric_lower or 'satış' in metric_lower:
                grouped_data[ad_name]['weeklyData']['purchases'] = weekly_values
            elif 'harcama' in metric_lower or 'spend' in metric_lower:
                grouped_data[ad_name]['weeklyData']['spend'] = weekly_values
            elif 'gelir' in metric_lower or 'revenue' in metric_lower:
                grouped_data[ad_name]['weeklyData']['revenue'] = weekly_values
            elif metric_lower == 'roas':
                grouped_data[ad_name]['weeklyData']['roas'] = weekly_values
        
        # Toplam değerleri hesapla ve eski format için ekle
        assets = []
        for idx, (ad_name, data) in enumerate(grouped_data.items(), 1):
            wd = data['weeklyData']
            
            # Toplamları hesapla
            total_impressions = sum(wd['impressions']) if wd['impressions'] else 0
            total_clicks = sum(wd['clicks']) if wd['clicks'] else 0
            total_spend = sum(wd['spend']) if wd['spend'] else 0
            total_purchases = sum(wd['purchases']) if wd['purchases'] else 0
            total_revenue = sum(wd['revenue']) if wd['revenue'] else 0
            
            # Ortalama/toplam CTR, CPC, ROAS
            avg_ctr = sum(wd['ctr']) / len(wd['ctr']) if wd['ctr'] else 0
            avg_cpc = sum(wd['cpc']) / len(wd['cpc']) if wd['cpc'] else 0
            total_roas = (total_revenue / total_spend) if total_spend > 0 else 0
            
            # Asset objesi oluştur (eski format + yeni weeklyData)
            asset = {
                'id': idx,
                'name': data['name'],
                'status': data['status'],
                'imageUrl': data['imageUrl'],
                'hasVideo': False,  # Bu bilgi sheet'te yoksa varsayılan
                
                # Toplam değerler (eski format için)
                'impression': int(total_impressions),
                'reach': int(total_impressions * 0.8),  # Yaklaşık reach (eğer sheet'te yoksa)
                'click': int(total_clicks),
                'ctr': round(avg_ctr, 2),
                'spend': round(total_spend, 2),
                'purchase': int(total_purchases),
                'revenue': round(total_revenue, 2),
                'roas': round(total_roas, 2),
                
                # Haftalık detay verisi
                'weeklyData': data['weeklyData']
            }
            
            assets.append(asset)
        
        return assets

    def do_OPTIONS(self):
        """CORS için OPTIONS request'i handle et"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
