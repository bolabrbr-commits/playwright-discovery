from playwright.sync_api import sync_playwright
import requests
from datetime import datetime
import time

# ================= CONFIG =================
HASHTAG = "didyouknow"   # sem #
MAX_RESULTS = 20
COUNTRY = "US"

WEBHOOK_URL = "https://n8n-n8n.rcjzpn.easypanel.host/webhook/shorts-discovery"
# =========================================

output = {
    "keyword": HASHTAG,
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

    hashtag_url = f"https://www.tiktok.com/tag/{HASHTAG}"
    page.goto(hashtag_url, timeout=60000)
    page.wait_for_timeout(4000)

    # scroll humano leve
    for _ in range(6):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(1200)

    # links de vídeos
    video_links = page.query_selector_all("a[href*='/video/']")

    for link in video_links:
        if len(output["videos"]) >= MAX_RESULTS:
            break

        try:
            href = link.get_attribute("href")
            text = link.inner_text()

            if not href:
                continue

            output["videos"].append({
                "title": text.strip() if text else "TikTok Curiosity",
                "url": href
            })

        except:
            continue

    browser.close()

# ========= ENVIO PARA N8N =========
print(f"Enviando {len(output['videos'])} vídeos para o Webhook...")

try:
    res = requests.post(
        WEBHOOK_URL,
        json=output,
        timeout=20
    )
    print("Webhook status:", res.status_code)
except Exception as e:
    print(f"Erro ao enviar webhook: {e}")

print("Videos sent:", len(output["videos"]))
