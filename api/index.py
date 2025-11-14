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
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({
                'error': str(e),
                'message': 'Veri çekme hatası'
            })
            self.wfile.write(error_response.encode('utf-8'))
    
    def parse_sheet_data(self, rows):
        """
        Google Sheets'teki haftalık raw data formatını parse eder
        AB sütunundaki Image URL'leri de dahil eder
        """
        
        # Header'ları al
        headers = [h.strip() for h in rows[0]]
        
        # Sütun indekslerini bul
        col_indices = {}
        for idx, header in enumerate(headers):
            header_lower = header.lower()
            if 'ad name' in header_lower:
                col_indices['ad_name'] = idx
            elif 'image url' in header_lower:
                col_indices['image_url'] = idx
            elif header_lower == 'week end' or 'week end' in header_lower:
                col_indices['week_end'] = idx
            elif header_lower == 'impressions':
                col_indices['impressions'] = idx
            elif header_lower == 'reach':
                col_indices['reach'] = idx
            elif header_lower == 'clicks':
                col_indices['clicks'] = idx
            elif header_lower == 'ctr':
                col_indices['ctr'] = idx
            elif header_lower == 'cpc':
                col_indices['cpc'] = idx
            elif header_lower == 'spend':
                col_indices['spend'] = idx
            elif 'purchase' in header_lower and 'count' in header_lower:
                col_indices['purchases'] = idx
            elif 'purchase value' in header_lower:
                col_indices['revenue'] = idx
            elif 'add to cart' in header_lower and 'count' in header_lower:
                col_indices['add_to_cart'] = idx
            elif 'view content' in header_lower and 'count' in header_lower:
                col_indices['view_content'] = idx
            elif 'video plays' in header_lower and 'any' in header_lower:
                col_indices['video_plays'] = idx
            elif 'quality ranking' in header_lower:
                col_indices['quality_ranking'] = idx
            elif 'engagement rate ranking' in header_lower:
                col_indices['engagement_ranking'] = idx
            elif 'conversion rate ranking' in header_lower:
                col_indices['conversion_ranking'] = idx
            elif header_lower == 'status':
                col_indices['status'] = idx
        
        if 'ad_name' not in col_indices:
            raise ValueError("Ad Name sütunu bulunamadı!")
        
        # Verileri grupla (Ad Name bazında)
        grouped_data = defaultdict(lambda: {
            'name': '',
            'status': 'ACTIVE',
            'imageUrl': '',
            'weeks': [],
            'weekly_metrics': []
        })
        
        # Her satırı işle
        for row in rows[1:]:
            if len(row) < 5:
                continue
            
            ad_name = row[col_indices['ad_name']].strip() if 'ad_name' in col_indices and col_indices['ad_name'] < len(row) else ''
            
            if not ad_name:
                continue
            
            # İlk defa görülen ad ise bilgileri kaydet
            if not grouped_data[ad_name]['name']:
                grouped_data[ad_name]['name'] = ad_name
                if 'status' in col_indices and col_indices['status'] < len(row):
                    status = row[col_indices['status']].strip()
                    grouped_data[ad_name]['status'] = status if status else 'ACTIVE'
                if 'image_url' in col_indices and col_indices['image_url'] < len(row):
                    image_url = row[col_indices['image_url']].strip()
                    grouped_data[ad_name]['imageUrl'] = image_url
            
            # Hafta bilgisini al
            week_end = row[col_indices['week_end']].strip() if 'week_end' in col_indices and col_indices['week_end'] < len(row) else ''
            
            # Metriği parse et
            def get_value(key, default=0):
                if key not in col_indices or col_indices[key] >= len(row):
                    return default
                value = row[col_indices[key]].strip()
                # Temizle: ₺, %, virgül vs.
                value = value.replace('₺', '').replace('%', '').replace(',', '').strip()
                try:
                    return float(value) if value else default
                except ValueError:
                    return default
            
            def get_string(key, default=''):
                if key not in col_indices or col_indices[key] >= len(row):
                    return default
                return row[col_indices[key]].strip()
            
            impressions = get_value('impressions', 0)
            reach = get_value('reach', 0)
            clicks = get_value('clicks', 0)
            ctr = get_value('ctr', 0)
            cpc = get_value('cpc', 0)
            spend = get_value('spend', 0)
            purchases = get_value('purchases', 0)
            revenue = get_value('revenue', 0)
            add_to_cart = get_value('add_to_cart', 0)
            view_content = get_value('view_content', 0)
            video_plays = get_value('video_plays', 0)
            quality_ranking = get_string('quality_ranking', 'UNKNOWN')
            engagement_ranking = get_string('engagement_ranking', 'UNKNOWN')
            conversion_ranking = get_string('conversion_ranking', 'UNKNOWN')
            
            # Haftalık veriyi ekle
            grouped_data[ad_name]['weeks'].append(week_end)
            grouped_data[ad_name]['weekly_metrics'].append({
                'impressions': impressions,
                'reach': reach,
                'clicks': clicks,
                'ctr': ctr,
                'cpc': cpc,
                'spend': spend,
                'purchases': purchases,
                'revenue': revenue,
                'roas': (revenue / spend) if spend > 0 else 0,
                'add_to_cart': add_to_cart,
                'view_content': view_content,
                'video_plays': video_plays,
                'quality_ranking': quality_ranking,
                'engagement_ranking': engagement_ranking,
                'conversion_ranking': conversion_ranking
            })
        
        # Asset objelerini oluştur
        assets = []
        for idx, (ad_name, data) in enumerate(grouped_data.items(), 1):
            if not data['weekly_metrics']:
                continue
            
            # Haftalık verileri dizilere dönüştür
            weeks = data['weeks']
            impressions = [m['impressions'] for m in data['weekly_metrics']]
            reaches = [m['reach'] for m in data['weekly_metrics']]
            clicks = [m['clicks'] for m in data['weekly_metrics']]
            ctrs = [m['ctr'] for m in data['weekly_metrics']]
            cpcs = [m['cpc'] for m in data['weekly_metrics']]
            spends = [m['spend'] for m in data['weekly_metrics']]
            purchases = [m['purchases'] for m in data['weekly_metrics']]
            revenues = [m['revenue'] for m in data['weekly_metrics']]
            roas_list = [m['roas'] for m in data['weekly_metrics']]
            add_to_carts = [m['add_to_cart'] for m in data['weekly_metrics']]
            view_contents = [m['view_content'] for m in data['weekly_metrics']]
            video_plays_list = [m['video_plays'] for m in data['weekly_metrics']]
            quality_rankings = [m['quality_ranking'] for m in data['weekly_metrics']]
            engagement_rankings = [m['engagement_ranking'] for m in data['weekly_metrics']]
            conversion_rankings = [m['conversion_ranking'] for m in data['weekly_metrics']]
            
            # Toplamları hesapla
            total_impressions = sum(impressions)
            total_reach = sum(reaches)
            total_clicks = sum(clicks)
            total_spend = sum(spends)
            total_purchases = sum(purchases)
            total_revenue = sum(revenues)
            total_add_to_cart = sum(add_to_carts)
            total_view_content = sum(view_contents)
            total_video_plays = sum(video_plays_list)
            
            # Ortalama CTR, CPC, ROAS
            avg_ctr = sum(ctrs) / len(ctrs) if ctrs else 0
            avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0
            total_roas = (total_revenue / total_spend) if total_spend > 0 else 0
            
            # Asset objesi oluştur
            asset = {
                'id': idx,
                'name': data['name'],
                'status': data['status'],
                'imageUrl': data['imageUrl'],
                'hasVideo': total_video_plays > 0,
                
                # Toplam değerler
                'impression': int(total_impressions),
                'reach': int(total_reach),
                'click': int(total_clicks),
                'ctr': round(avg_ctr, 2),
                'spend': round(total_spend, 2),
                'purchase': int(total_purchases),
                'revenue': round(total_revenue, 2),
                'roas': round(total_roas, 2),
                'add_to_cart': int(total_add_to_cart),
                'view_content': int(total_view_content),
                'video_plays': int(total_video_plays),
                
                # Haftalık detay verisi
                'weeklyData': {
                    'weeks': weeks,
                    'impressions': impressions,
                    'clicks': clicks,
                    'ctr': ctrs,
                    'cpc': cpcs,
                    'spend': spends,
                    'purchases': purchases,
                    'revenue': revenues,
                    'roas': roas_list,
                    'add_to_cart': add_to_carts,
                    'view_content': view_contents,
                    'video_plays': video_plays_list,
                    'quality_ranking': quality_rankings,
                    'engagement_ranking': engagement_rankings,
                    'conversion_ranking': conversion_rankings
                }
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
