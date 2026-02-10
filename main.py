import base64
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

app = FastAPI()

GEMINI_URL = "https://gemini.google.com/app"


class ImageRequest(BaseModel):
    scene_prompt: str
    character_image_url: str


def download_image(url, path):
    r = requests.get(url)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)


def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


@app.post("/generate-image")
def generate_image(data: ImageRequest):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        page.goto(GEMINI_URL, timeout=60000)
        page.wait_for_timeout(5000)

        character_path = "/tmp/character.png"
        output_path = "/tmp/output.png"

        download_image(data.character_image_url, character_path)

        page.locator("input[type=file]").set_input_files(character_path)
        page.wait_for_timeout(3000)

        textarea = page.locator("textarea")
        textarea.fill(f"""
Use the uploaded image as the SAME CHARACTER reference.

Create a cinematic, ultra realistic image.

Scene:
{data.scene_prompt}

Rules:
- same character
- same face
- no text
- no logos
- 16:9
""")
        textarea.press("Enter")

        page.wait_for_timeout(15000)

        page.locator("img").first.screenshot(path=output_path)

        browser.close()

        return {
            "status": "ok",
            "image_base64": image_to_base64(output_path)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
