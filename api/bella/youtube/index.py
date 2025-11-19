# api/bella/youtube/index.py
# Bella Maison YouTube Ad Report -> VI zone dashboard JSON
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen
import csv
import io
import json
from datetime import datetime, timedelta
from collections import defaultdict

# === CONFIG ===
SHEET_ID = "1kgdsxbF4UkLyJi9j1zQPyyQ-q2sUROV9MED0DTinVEg"
GID = "1743463769"  # Y tab

# CSV export endpoint
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"


def parse_float(value):
    """Para birimi ve yüzde işaretlerini temizler."""
    if value is None:
        return 0.0
    v = str(value).strip()
    if v == "" or v.upper() == "NA":
        return 0.0

    # $ ve % temizle
    v = v.replace("$", "").replace("%", "").replace(" ", "")

    # Hem nokta hem virgül varsa -> nokta binliktir
    if "," in v and "." in v:
        v = v.replace(",", "")
    elif "," in v:
        v = v.replace(",", ".")

    try:
        return float(v)
    except ValueError:
        return 0.0


def parse_int(value):
    return int(round(parse_float(value)))


def parse_date(date_str):
    """Tarihi YYYY-MM-DD formatından hafta başlangıcına çevirir."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Haftanın ilk günü Pazartesi
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        return start_of_week.strftime("%Y-%m-%d")
    except:
        return date_str


def fetch_rows():
    """Sheet'i CSV olarak indirip DictReader ile satır listesi döner."""
    with urlopen(CSV_URL) as resp:
        data = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(data))
    return list(reader)


def build_assets(rows):
    """
    Satırları 'Ad' (reklam adı) bazında grupla ve haftalık verilere dönüştür.
    """
    # Önce günlük verileri haftalık gruplara dönüştür
    weekly_data = defaultdict(lambda: defaultdict(lambda: {
        "impressions": 0,
        "clicks": 0,
        "cost": 0.0,
        "conversions": 0,
        "conv_value": 0.0,
        "views": 0,
        "video_25": 0.0,
        "video_50": 0.0,
        "video_75": 0.0,
        "video_100": 0.0,
        "days_count": 0,
        "image_url": "",
    }))

    for row in rows:
        ad_name = (row.get("Ad") or "").strip()
        if not ad_name:
            continue

        day = (row.get("Day") or "").strip()
        if not day:
            continue

        week = parse_date(day)
        image_url = (row.get("Image") or "").strip()

        # Metrikler
        impressions = parse_int(row.get("Impr."))
        clicks = parse_int(row.get("Clicks"))
        cost = parse_float(row.get("Cost"))
        conversions = parse_int(row.get("Conversions"))
        conv_value = parse_float(row.get("Conv. value"))
        views = parse_int(row.get("Views"))
        
        # Video completion rates (yüzde formatında)
        video_25 = parse_float(row.get("Video played to 25%"))
        video_50 = parse_float(row.get("Video played to 50%"))
        video_75 = parse_float(row.get("Video played to 75%"))
        video_100 = parse_float(row.get("Video played to 100%"))

        # Haftalık verileri topla
        week_data = weekly_data[ad_name][week]
        week_data["impressions"] += impressions
        week_data["clicks"] += clicks
        week_data["cost"] += cost
        week_data["conversions"] += conversions
        week_data["conv_value"] += conv_value
        week_data["views"] += views
        week_data["video_25"] += video_25
        week_data["video_50"] += video_50
        week_data["video_75"] += video_75
        week_data["video_100"] += video_100
        week_data["days_count"] += 1
        
        if image_url and not week_data["image_url"]:
            week_data["image_url"] = image_url

    # Asset objelerini oluştur
    assets = []
    for idx, (ad_name, weeks_dict) in enumerate(weekly_data.items(), 1):
        weeks = sorted(weeks_dict.keys())
        
        # Haftalık dizileri oluştur
        weekly_metrics = {
            "weeks": [],
            "impressions": [],
            "clicks": [],
            "ctr": [],
            "cost": [],
            "cpc": [],
            "conversions": [],
            "conv_value": [],
            "cvr": [],
            "cpa": [],
            "views": [],
            "vtr": [],
            "video_25": [],
            "video_50": [],
            "video_75": [],
            "video_100": [],
        }

        total_impressions = 0
        total_clicks = 0
        total_cost = 0.0
        total_conversions = 0
        total_conv_value = 0.0
        total_views = 0
        image_url = ""

        for week in weeks:
            week_data = weeks_dict[week]
            
            impressions = week_data["impressions"]
            clicks = week_data["clicks"]
            cost = week_data["cost"]
            conversions = week_data["conversions"]
            conv_value = week_data["conv_value"]
            views = week_data["views"]
            days = week_data["days_count"]

            # Ortalama completion rates (günlük ortalamaları)
            video_25 = week_data["video_25"] / days if days > 0 else 0
            video_50 = week_data["video_50"] / days if days > 0 else 0
            video_75 = week_data["video_75"] / days if days > 0 else 0
            video_100 = week_data["video_100"] / days if days > 0 else 0

            # Hesaplanan metrikler
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cpc = (cost / clicks) if clicks > 0 else 0
            cvr = (conversions / clicks * 100) if clicks > 0 else 0
            cpa = (cost / conversions) if conversions > 0 else 0
            vtr = (views / impressions * 100) if impressions > 0 else 0

            # Haftalık verileri ekle
            weekly_metrics["weeks"].append(week)
            weekly_metrics["impressions"].append(impressions)
            weekly_metrics["clicks"].append(clicks)
            weekly_metrics["ctr"].append(round(ctr, 2))
            weekly_metrics["cost"].append(round(cost, 2))
            weekly_metrics["cpc"].append(round(cpc, 2))
            weekly_metrics["conversions"].append(conversions)
            weekly_metrics["conv_value"].append(round(conv_value, 2))
            weekly_metrics["cvr"].append(round(cvr, 2))
            weekly_metrics["cpa"].append(round(cpa, 2))
            weekly_metrics["views"].append(views)
            weekly_metrics["vtr"].append(round(vtr, 2))
            weekly_metrics["video_25"].append(round(video_25, 2))
            weekly_metrics["video_50"].append(round(video_50, 2))
            weekly_metrics["video_75"].append(round(video_75, 2))
            weekly_metrics["video_100"].append(round(video_100, 2))

            # Toplamları hesapla
            total_impressions += impressions
            total_clicks += clicks
            total_cost += cost
            total_conversions += conversions
            total_conv_value += conv_value
            total_views += views
            
            if week_data["image_url"]:
                image_url = week_data["image_url"]

        # Toplam metrikler
        total_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        total_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
        total_cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        total_cpa = (total_cost / total_conversions) if total_conversions > 0 else 0
        total_vtr = (total_views / total_impressions * 100) if total_impressions > 0 else 0
        total_roas = (total_conv_value / total_cost) if total_cost > 0 else 0

        asset = {
            "id": idx,
            "name": ad_name,
            "status": "ACTIVE",
            "imageUrl": image_url,
            "hasVideo": True,
            
            # Toplam değerler
            "impression": total_impressions,
            "click": total_clicks,
            "ctr": round(total_ctr, 2),
            "spend": round(total_cost, 2),
            "cpc": round(total_cpc, 2),
            "conversion": total_conversions,
            "conv_value": round(total_conv_value, 2),
            "cvr": round(total_cvr, 2),
            "cpa": round(total_cpa, 2),
            "roas": round(total_roas, 2),
            "views": total_views,
            "vtr": round(total_vtr, 2),
            
            # Haftalık detay verisi
            "weeklyData": weekly_metrics
        }
        
        assets.append(asset)

    return assets


class handler(BaseHTTPRequestHandler):
    """Vercel Python Function için HTTP handler."""

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
            rows = fetch_rows()
            assets = build_assets(rows)
            body = json.dumps(assets, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            error = {"error": str(e)}
            body = json.dumps(error, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self._set_cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
