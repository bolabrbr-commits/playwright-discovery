from playwright.sync_api import sync_playwright
import requests
from datetime import datetime
import time

# ================= CONFIG =================
KEYWORD = "storytime"        # nicho principal
MAX_RESULTS = 20             # limite por execução
COUNTRY = "US"               # etiqueta (não força geo real)
SCROLL_TIMES = 8             # controla volume / risco

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

    # ===== FEED DIRETO DE SHORTS (mais estável que search) =====
    page.goto("https://www.youtube.com/shorts", timeout=60000)
    page.wait_for_timeout(4000)

    # Scroll humano leve (baixo risco)
    for _ in range(SCROLL_TIMES):
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(1200)

    # Coleta links de Shorts
    links = page.query_selector_all("a[href^='/shorts/']")

    for link in links:
        if len(output["videos"]) >= MAX_RESULTS:
            break

        try:
            href = link.get_attribute("href")
            title = link.inner_text()

            if not href:
                continue

            output["videos"].append({
                "title": title.strip() if title else "YouTube Short",
                "url": "https://www.youtube.com" + href
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

print("Shorts sent:", len(output["videos"]))
