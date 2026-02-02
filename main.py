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

    # URL com filtro de Shorts forçado (sp=EgIYAw%253D%253D)
    search_url = f"https://www.youtube.com/results?search_query={KEYWORD}&sp=EgIYAw%253D%253D"
    page.goto(search_url, timeout=60000)
    page.wait_for_timeout(3000)

    # Força scroll para carregar Shorts
    for _ in range(6):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(1200)

    # ================= SOLUÇÃO HÍBRIDA =================
    # 1. Tenta pegar pelo container oficial (mais rico em dados)
    shorts = page.query_selector_all("ytd-reel-item-renderer")
    
    # 2. Se falhar (retornar vazio), ativa o fallback para links brutos
    if not shorts:
        print("⚠️ Container padrão não encontrado. Ativando fallback para links...")
        shorts = page.query_selector_all("a[href*='/shorts/']")
    # ===================================================

    for el in shorts:
        if len(output["videos"]) >= MAX_RESULTS:
            break

        try:
            # Lógica Híbrida: Verifica se é um Link (Fallback) ou Container (Renderer)
            if el.get_attribute("href"):
                # É o caso do fallback (elemento <a>)
                href = el.get_attribute("href")
                title = el.inner_text() # Tenta pegar texto do link
                if not title: # Se vier vazio, tenta título acessível ou ignora
                    title = "Short sem título"
            else:
                # É o caso do renderer (elemento <ytd-reel...>)
                title_el = el.query_selector("#video-title")
                link_el = el.query_selector("a")

                if not title_el or not link_el:
                    continue

                href = link_el.get_attribute("href")
                title = title_el.inner_text()

            # Validação final de segurança
            if not href or "/shorts/" not in href:
                continue

            output["videos"].append({
                "title": title.strip(),
                "url": "https://www.youtube.com" + href
            })

        except Exception as e:
            # print(f"Erro ao processar item: {e}") 
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
