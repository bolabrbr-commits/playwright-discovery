from playwright.sync_api import sync_playwright
import requests
from datetime import datetime

# ================= CONFIG =================
KEYWORD = "storytime"
MAX_RESULTS = 20
COUNTRY = "US"

WEBHOOK_URL = "https://n8n-n8n.rcjzpn.easypanel.host/webhook/shorts-discovery"
# ==========================================

def score_video(title, published):
    score = 0

    if title:
        t = title.lower()
        if any(w in t for w in ["story", "storytime", "true", "real"]):
            score += 3
        if len(title) < 70:
            score += 1

    if published:
        if "minute" in published or "hour" in published:
            score += 3
        elif "day" in published:
            score += 1

    return score


payload = {
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
            "--single-process",
            "--no-zygote",
        ]
    )

    context = browser.new_context(
        locale="en-US",
        timezone_id="America/New_York"
    )

    page = context.new_page()
    page.goto(
        f"https://www.youtube.com/results?search_query={KEYWORD}&sp=CAISAhAB",
        timeout=60000
    )
    page.wait_for_timeout(5000)

    videos = page.query_selector_all("ytd-video-renderer")

    for video in videos[:MAX_RESULTS]:
        try:
            title_el = video.query_selector("#video-title")
            channel_el = video.query_selector("ytd-channel-name a")
            time_el = video.query_selector("span.inline-metadata-item")

            if not title_el:
                continue

            title = title_el.inner_text().strip()
            url = "https://www.youtube.com" + title_el.get_attribute("href")
            channel = channel_el.inner_text().strip() if channel_el else None
            published = time_el.inner_text().strip() if time_el else None

            payload["videos"].append({
                "title": title,
                "url": url,
                "channel": channel,
                "published": published,
                "score": score_video(title, published)
            })

        except:
            continue

    browser.close()

# ======= SEND TO N8N =======
response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
print("Webhook status:", response.status_code)
print("Videos sent:", len(payload["videos"]))
