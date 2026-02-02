from playwright.sync_api import sync_playwright
import requests
from datetime import datetime
import time

# ================= CONFIG =================
KEYWORD = "storytime"
MAX_RESULTS = 20
COUNTRY = "US"

WEBHOOK_URL = "https://n8n-n8n.rcjzpn.easypanel.host/webhook/shorts-discovery"
# =========================================

output = {
    "keyword": KEYWORD,
    "country": COUNTRY,
    "collected_at": datetime.utcnow().isoformat(),
    "videos": []
}

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )

    context = browser.new_context(
        locale="en-US",
        timezone_id="America/New_York",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9"
        }
    )

    page = context.new_page()

    search_url = f"https://www.youtube.com/results?search_query={KEYWORD}&sp=EgIYAw%253D%253D"
    page.goto(search_url, timeout=60000)

    # tempo para carregar shorts
    page.wait_for_timeout(5000)

    # pega SOMENTE shorts
    shorts = page.query_selector_all("ytd-reel-item-renderer")

    for short in shorts:
        if len(output["videos"]) >= MAX_RESULTS:
            break

        try:
            title_el = short.query_selector("#video-title")
            link_el = short.query_selector("a")

            if not title_el or not link_el:
                continue

            href = link_el.get_attribute("href")

            # valida que é shorts
            if not href or "/shorts/" not in href:
                continue

            output["videos"].append({
                "title": title_el.inner_text().strip(),
                "url": "https://www.youtube.com" + href
            })

        except:
            continue

    browser.close()

# ========= ENVIO PARA N8N =========
res = requests.post(
    WEBHOOK_URL,
    json=output,
    timeout=20
)

print("Webhook status:", res.status_code)
print("Shorts sent:", len(output["videos"]))
