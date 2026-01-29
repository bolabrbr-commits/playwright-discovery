from playwright.sync_api import sync_playwright
import time

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

    page = browser.new_page()
    page.goto("https://www.youtube.com/results?search_query=storytime&sp=CAISAhAB")
    time.sleep(5)

    videos = page.query_selector_all("#video-title")
    for v in videos[:10]:
        print(v.inner_text())

    browser.close()
