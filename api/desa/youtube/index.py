# api/desa/youtube/index.py
# Desa YouTube Ad Report -> VI zone dashboard JSON (FIXED)
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen
import csv
import io
import json
from datetime import datetime, timedelta
from collections import defaultdict

# === CONFIG - DESA ===
SHEET_ID = "1XJfW08gLJomg9ZYjJug_jDmhWs-eop3s0LOhEVo7VRA"
GID = "1208036518"

# CSV export endpoint
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"


def parse_float(value):
    """Para birimi ve yüzde işaretlerini temizler."""
    if value is None:
        return 0.0
    v = str(value).strip()
    if v == "" or v.upper() == "NA" or v == "N/A":
        return 0.0

    # Temizlik
    v = v.replace("$", "").replace("%", "").replace(" ", "").replace("₺", "").replace(",", "")

    try:
        return float(v)
    except ValueError:
        return 0.0


def parse_int(value):
    try:
        return int(round(parse_float(value)))
    except:
        return 0


def parse_week(week_str):
    """Week formatını YYYY-MM-DD formatına çevirir."""
    if not week_str or week_str.strip() == "":
        return ""
    
    week_str = week_str.strip()
    
    # Eğer zaten YYYY-MM-DD formatındaysa
    if "-" in week_str and len(week_str) == 10:
        return week_str
    
    # 2025-W18 formatını parse et
    if "W" in week_str.upper():
        try:
            # 2025-W18 veya W18 formatını ayır
            parts = week_str.split('-')
            if len(parts) == 2:  # 2025-W18
                year = int(parts[0])
                week_num = int(parts[1].upper().replace('W', ''))
            else:  # W18
                year = 2025  # Varsayılan yıl
                week_num = int(week_str.upper().replace('W', ''))
            
            # ISO 8601: Yılın ilk Perşembesini içeren hafta, 1. haftadır
            jan_4 = datetime(year, 1, 4)
            week_start = jan_4 - timedelta(days=jan_4.weekday())
            target_week_start = week_start + timedelta(weeks=week_num - 1)
            
            return target_week_start.strftime("%Y-%m-%d")
        except:
            return week_str
    
    return week_str


def fetch_rows():
    """Sheet'i CSV olarak indirip DictReader ile satır listesi döner."""
    with urlopen(CSV_URL) as resp:
        data = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(data))
    return list(reader)


def build_assets(rows):
    """
    Satırları 'VideoTitle' (reklam adı) bazında grupla ve haftalık verilere dönüştür.
    """
    if not rows:
        return []
    
    # Haftalık verileri grupla
    weekly_data = defaultdict(lambda: defaultdict(lambda: {
        "impressions": 0,
        "clicks": 0,
        "ctr": 0.0,
        "cpv": 0.0,
        "cost": 0.0,
        "conversions": 0,
        "conv_value": 0.0,
        "views": 0,
        "view_rate": 0.0,
        "video_25": 0.0,
        "video_50": 0.0,
        "video_75": 0.0,
        "video_100": 0.0,
        "days_count": 0,
        "thumbnail_url": "",
    }))

    for row in rows:
        # Reklam adı (VideoTitle kullan)
        ad_name = (row.get("VideoTitle") or row.get("Video Title") or "").strip()
        if not ad_name:
            continue

        # Hafta bilgisi
        week = parse_week(row.get("Week") or "")
        if not week:
            continue

        thumbnail_url = (row.get("ThumbnailUrl") or row.get("Thumbnail Url") or "").strip()

        # Metrikler - Sheet'ten gelen değerler
        impressions = parse_int(row.get("Impressions"))
        clicks = parse_int(row.get("Clicks"))
        ctr = parse_float(row.get("CTR"))  # Zaten yüzde cinsinden geliyor
        cpv = parse_float(row.get("AverageCpv") or row.get("Average Cpv"))
        cost = parse_float(row.get("Cost"))
        conversions = parse_int(row.get("Conversions"))
        conv_value = parse_float(row.get("ConversionValue") or row.get("Conversion Value"))
        views = parse_int(row.get("VideoViews") or row.get("Video Views"))
        view_rate = parse_float(row.get("ViewRate") or row.get("View Rate"))
        
        # Video completion rates (yüzde formatında)
        video_25 = parse_float(row.get("VideoQuartile25Rate") or row.get("Video Quartile 25 Rate"))
        video_50 = parse_float(row.get("VideoQuartile50Rate") or row.get("Video Quartile 50 Rate"))
        video_75 = parse_float(row.get("VideoQuartile75Rate") or row.get("Video Quartile 75 Rate"))
        video_100 = parse_float(row.get("VideoQuartile100Rate") or row.get("Video Quartile 100 Rate"))

        # Haftalık verileri topla
        week_data = weekly_data[ad_name][week]
        week_data["impressions"] += impressions
        week_data["clicks"] += clicks
        week_data["ctr"] += ctr
        week_data["cpv"] += cpv
        week_data["cost"] += cost
        week_data["conversions"] += conversions
        week_data["conv_value"] += conv_value
        week_data["views"] += views
        week_data["view_rate"] += view_rate
        week_data["video_25"] += video_25
        week_data["video_50"] += video_50
        week_data["video_75"] += video_75
        week_data["video_100"] += video_100
        week_data["days_count"] += 1
        
        if thumbnail_url and not week_data["thumbnail_url"]:
            week_data["thumbnail_url"] = thumbnail_url

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
        thumbnail_url = ""

        for week in weeks:
            week_data = weeks_dict[week]
            
            impressions = week_data["impressions"]
            clicks = week_data["clicks"]
            cost = week_data["cost"]
            conversions = week_data["conversions"]
            conv_value = week_data["conv_value"]
            views = week_data["views"]
            days = week_data["days_count"]

            # Ortalama metrikler (günlük ortalamaları)
            ctr = week_data["ctr"] / days if days > 0 else 0  # Zaten yüzde
            view_rate = week_data["view_rate"] / days if days > 0 else 0  # Zaten yüzde
            video_25 = week_data["video_25"] / days if days > 0 else 0
            video_50 = week_data["video_50"] / days if days > 0 else 0
            video_75 = week_data["video_75"] / days if days > 0 else 0
            video_100 = week_data["video_100"] / days if days > 0 else 0

            # Hesaplanan metrikler
            cpc = (cost / clicks) if clicks > 0 else 0
            cvr = (conversions / clicks * 100) if clicks > 0 else 0
            cpa = (cost / conversions) if conversions > 0 else 0
            vtr = view_rate

            # Haftalık verileri ekle - 0 değerleri de dahil et
            weekly_metrics["weeks"].append(week)
            weekly_metrics["impressions"].append(impressions if impressions > 0 else 0)
            weekly_metrics["clicks"].append(clicks if clicks > 0 else 0)
            weekly_metrics["ctr"].append(round(ctr, 2) if ctr > 0 else 0)
            weekly_metrics["cost"].append(round(cost, 2) if cost > 0 else 0)
            weekly_metrics["cpc"].append(round(cpc, 2) if cpc > 0 else 0)
            weekly_metrics["conversions"].append(conversions if conversions > 0 else 0)
            weekly_metrics["conv_value"].append(round(conv_value, 2) if conv_value > 0 else 0)
            weekly_metrics["cvr"].append(round(cvr, 2) if cvr > 0 else 0)
            weekly_metrics["cpa"].append(round(cpa, 2) if cpa > 0 else 0)
            weekly_metrics["views"].append(views if views > 0 else 0)
            weekly_metrics["vtr"].append(round(vtr, 2) if vtr > 0 else 0)
            weekly_metrics["video_25"].append(round(video_25, 2) if video_25 > 0 else 0)
            weekly_metrics["video_50"].append(round(video_50, 2) if video_50 > 0 else 0)
            weekly_metrics["video_75"].append(round(video_75, 2) if video_75 > 0 else 0)
            weekly_metrics["video_100"].append(round(video_100, 2) if video_100 > 0 else 0)

            # Toplamları hesapla
            total_impressions += impressions
            total_clicks += clicks
            total_cost += cost
            total_conversions += conversions
            total_conv_value += conv_value
            total_views += views
            
            if week_data["thumbnail_url"]:
                thumbnail_url = week_data["thumbnail_url"]

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
            "imageUrl": thumbnail_url,
            "hasVideo": True,
            "labels": ["video"],
            
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
            error = {"error": str(e), "type": type(e).__name__}
            body = json.dumps(error, ensure_ascii=False).encode("utf-8")
            self.send_response(500)
            self._set_cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
