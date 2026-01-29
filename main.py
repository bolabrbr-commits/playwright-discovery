from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

KEYWORD = "storytime"
MAX_RESULTS = 15
COUNTRY = "US"

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
            "--single-process",
            "--no-zygote",
        ]
    )

    context = browser.new_context(
        locale="en-US",
        timezone_id="America/New_York"
    )

    page = context.new_page()

    search_url = f"https://www.youtube.com/results?search_query={KEYWORD}&sp=CAISAhAB"
    page.goto(search_url, timeout=60000)
    page.wait_for_timeout(5000)

    videos = page.query_selector_all("ytd-video-renderer")

    for video in videos[:MAX_RESULTS]:
        try:
            title_el = video.query_selector("#video-title")
            channel_el = video.query_selector("ytd-channel-name a")
            time_el = video.query_selector("span.inline-metadata-item")

            if not title_el:
                continue

            output["videos"].append({
                "title": title_el.inner_text().strip(),
                "url": "https://www.youtube.com" + title_el.get_attribute("href"),
                "channel": channel_el.inner_text().strip() if channel_el else None,
                "published": time_el.inner_text().strip() if time_el else None
            })

        except:
            continue

    browser.close()

with open("shorts_discovery.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Discovery finished. Videos found:", len(output["videos"]))
