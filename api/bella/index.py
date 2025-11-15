# api/index.py
# Bella Maison Ad Report -> VI zone dashboard JSON
from http.server import BaseHTTPRequestHandler
from urllib.request import urlopen
import csv
import io
import json

# === CONFIG ===
SHEET_ID = "1qUwEr5qhDCNKrTpS6JILY3aWyWeRUtjNt0wCHCPnXlI"
GID = "1154878507"

# CSV export endpoint
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"


def parse_float(value):
    """Türk formatlı sayıları da tolere edecek şekilde float'a çevirir."""
    if value is None:
        return 0.0
    v = str(value).strip()
    if v == "" or v.upper() == "NA":
        return 0.0

    # Para işaretleri, yüzde vb. temizle
    v = (
        v.replace("₺", "")
        .replace("%", "")
        .replace(" ", "")
    )

    # Hem nokta hem virgül varsa -> nokta binliktir, virgül ondalık
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")

    try:
        return float(v)
    except ValueError:
        return 0.0


def parse_int(value):
    return int(round(parse_float(value)))


def fetch_rows():
    """Sheet'i CSV olarak indirip DictReader ile satır listesi döner."""
    with urlopen(CSV_URL) as resp:
        data = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(data))
    return list(reader)


def build_assets(rows):
    """
    Satırları 'Ad Name' bazında gruplayıp VI zone dashboard'un
    beklediği JSON formatına dönüştürür.
    """
    assets = {}

    for row in rows:
        ad_name = (row.get("Ad Name") or "").strip()
        if not ad_name:
            continue

        key = ad_name  # Gerekirse image URL vs. ile birleştirip daha granular yapabilirsin

        week = (row.get("Week Start") or "").strip() or (row.get("Period") or "").strip()
        status = (row.get("Status") or "").strip()
        image_url = (row.get("Image URL") or "").strip()

        if key not in assets:
            assets[key] = {
                "id": len(assets) + 1,
                "name": ad_name,
                "status": status,
                "imageUrl": image_url,
                "weeklyData": {
                    "weeks": [],
                    "clicks": [],
                    "ctr": [],
                    "cpc": [],
                    "purchases": [],
                    "spend": [],
                    "revenue": [],
                    "impressions": [],
                    "reach": [],
                    "frequency": [],
                    "cpm": [],
                    "add_to_cart": [],
                    "view_content": [],
                    "video_plays": [],
                    "video_25": [],
                    "video_50": [],
                    "video_75": [],
                    "video_95": [],
                    "video_avg_watch": [],
                    "quality_ranking": [],
                    "engagement_ranking": [],
                    "conversion_ranking": [],
                    "days_live": [],
                },
            }

        asset = assets[key]
        wd = asset["weeklyData"]

        # Haftayı ekle
        wd["weeks"].append(week)

        # Performans metrikleri
        wd["clicks"].append(parse_int(row.get("Clicks")))
        wd["ctr"].append(parse_float(row.get("CTR")))
        wd["cpc"].append(parse_float(row.get("CPC")))
        wd["purchases"].append(parse_int(row.get("Purchases (count)")))
        wd["spend"].append(parse_float(row.get("Spend")))
        wd["revenue"].append(parse_float(row.get("Purchase Value")))

        # Engagement metrikleri
        wd["impressions"].append(parse_int(row.get("Impressions")))
        wd["reach"].append(parse_int(row.get("Reach")))
        wd["frequency"].append(parse_float(row.get("Frequency")))
        wd["cpm"].append(parse_float(row.get("CPM")))
        wd["add_to_cart"].append(parse_int(row.get("Add to Cart (count)")))
        wd["view_content"].append(parse_int(row.get("View Content (count)")))

        # Video metrikleri
        wd["video_plays"].append(parse_int(row.get("Video Plays (Any)")))
        wd["video_25"].append(parse_int(row.get("Video 25% Plays")))
        wd["video_50"].append(parse_int(row.get("Video 50% Plays")))
        wd["video_75"].append(parse_int(row.get("Video 75% Plays")))
        wd["video_95"].append(parse_int(row.get("Video 95% Plays")))
        wd["video_avg_watch"].append(parse_float(row.get("Video Avg Watch Time (s)")))

        # Ranking'ler
        wd["quality_ranking"].append((row.get("Quality Ranking") or "").strip())
        wd["engagement_ranking"].append((row.get("Engagement Rate Ranking") or "").strip())
        wd["conversion_ranking"].append((row.get("Conversion Rate Ranking") or "").strip())

        # Days Live
        wd["days_live"].append(parse_int(row.get("Days Live")))

        # Son boş olmayan status / image'ı yukarı yaz
        if status:
            asset["status"] = status
        if image_url:
            asset["imageUrl"] = image_url

    def sum_list(lst):
        return float(sum(x or 0 for x in lst))

    # Top-level KPI'lar
    for asset in assets.values():
        wd = asset["weeklyData"]
        clicks = sum_list(wd["clicks"])
        spend = sum_list(wd["spend"])
        revenue = sum_list(wd["revenue"])
        purchases = sum_list(wd["purchases"])

        asset["click"] = clicks
        asset["spend"] = spend
        asset["revenue"] = revenue
        asset["purchase"] = purchases
        asset["roas"] = (revenue / spend) if spend > 0 else 0.0

    return list(assets.values())


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
