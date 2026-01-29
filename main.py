from playwright.sync_api import sync_playwright
import json
from datetime import datetime

KEYWORD = "storytime"
MAX_RESULTS = 20
COUNTRY = "US"

def score_video(title, published):
    score = 0

    if title:
        title_l = title.lower()
        if any(w in title_l for w in ["story", "storytime", "true", "real"]):
            score += 3
        if len(title) < 70:
            score += 1

    if published:
        if "hour" in published or "minute" in published:
            score += 3
        elif "day" in published:
            score += 1

    return score


raw_output = {
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

            score = score_video(title, published)

            raw_output["videos"].append({
                "title": title,
                "url": url,
                "channel": channel,
                "published": published,
                "score": score
            })

        except:
            continue

    browser.close()

# salvar bruto
with open("shorts_discovery_raw.json", "w", encoding="utf-8") as f:
    json.dump(raw_output, f, ensure_ascii=False, indent=2)

# ordenar por score
ranked = sorted(raw_output["videos"], key=lambda x: x["score"], reverse=True)

with open("shorts_ranked.json", "w", encoding="utf-8") as f:
    json.dump(ranked, f, ensure_ascii=False, indent=2)

print("Discovery finished.")
print("Total videos:", len(raw_output["videos"]))
print("Top score:", ranked[0]["score"] if ranked else "none")
