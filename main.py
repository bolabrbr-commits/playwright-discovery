from playwright.sync_api import sync_playwright
import requests
from datetime import datetime

KEYWORD = "storytime"
MAX_RESULTS = 15
COUNTRY = "US"

WEBHOOK_URL = "https://n8n-n8n.rcjzpn.easypanel.host/webhook/shorts-discovery"

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

    page = browser.new_page()
    page.goto(
        f"https://www.youtube.com/results?search_query={KEYWORD}&sp=CAISAhAB",
        timeout=60000
    )
    page.wait_for_timeout(5000)

    videos = page.query_selector_all("ytd-video-renderer")

    for video in videos[:MAX_RESULTS]:
        title_el = video.query_selector("#video-title")
        if not title_el:
            continue

        output["videos"].append({
            "title": title_el.inner_text().strip(),
            "url": "https://www.youtube.com" + title_el.get_attribute("href"),
        })

    browser.close()

res = requests.post(WEBHOOK_URL, json=output, timeout=20)
print("Webhook status:", res.status_code)
print("Videos sent:", len(output["videos"]))
