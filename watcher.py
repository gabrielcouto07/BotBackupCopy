import re
import hashlib
import base64
import uuid
from pathlib import Path
from datetime import datetime
from playwright.async_api import Page, Locator

async def open_chat(page: Page, chat_name: str):
    search_box = page.locator("div[contenteditable='true'][data-tab='3']")
    await search_box.click()
    await page.wait_for_timeout(300)
    await search_box.press("Control+A")
    await page.wait_for_timeout(100)
    await search_box.press("Backspace")
    await page.wait_for_timeout(200)
    await search_box.type(chat_name, delay=50)
    await page.wait_for_timeout(1000)
    chat_item = page.locator(f"span[title='{chat_name}']").first
    await chat_item.click()
    await page.wait_for_timeout(600)

async def get_last_message_bubble(page: Page) -> Locator | None:
    bubbles = page.locator("div.message-in, div.message-out")
    count = await bubbles.count()
    if count == 0:
        return None
    return bubbles.nth(count - 1)

async def extract_last_message_text_and_urls(page) -> tuple[str, list[str]]:
    last = await get_last_message_bubble(page)
    if last is None:
        return "", []
    hrefs = []
    try:
        hrefs = await last.locator("a[href^='http']").evaluate_all(
            "els => els.map(a => a.getAttribute('href')).filter(Boolean)",
            timeout=5000,
        )
        hrefs = [h.strip() for h in hrefs if isinstance(h, str) and h.strip()]
    except Exception:
        pass
    raw_text = ""
    try:
        copyable = last.locator("span.copyable-text").first
        raw_text = await copyable.evaluate(
            """
            el => {
                let text = '';
                function extract(node) {
                    if (node.nodeType === 3) {
                        text += node.textContent;
                    } else if (node.nodeType === 1) {
                        const tag = node.tagName;
                        if (tag === 'IMG' && node.classList.contains('emoji')) {
                            text += node.alt || '';
                        } else if (tag === 'STRONG') {
                            text += '*';
                            node.childNodes.forEach(extract);
                            text += '*';
                        } else if (tag === 'EM') {
                            text += '_';
                            node.childNodes.forEach(extract);
                            text += '_';
                        } else if (tag === 'BR') {
                            text += '\\n';
                        } else {
                            node.childNodes.forEach(extract);
                        }
                    }
                }
                extract(el);
                return text;
            }
            """,
            timeout=8000,
        )
    except Exception:
        try:
            copyable = last.locator("span.copyable-text").first
            raw_text = await copyable.inner_text(timeout=5000)
        except Exception:
            try:
                raw_text = await last.inner_text(timeout=5000)
            except Exception as e:
                print(f"   ⚠️ Não foi possível extrair texto (timeout): {e}")
                return "", hrefs
    raw_text = (raw_text or "").strip()
    lines = []
    for ln in raw_text.splitlines():
        ln_stripped = ln.strip()
        ln_lower = ln_stripped.lower()
        if ln_lower in ("encaminhada", "forwarded"):
            continue
        if (
            ln_stripped
            and len(ln_stripped) <= 8
            and re.match(r"^\d{1,2}:\d{2}(\s?(AM|PM|am|pm))?$", ln_stripped)
        ):
            continue
        lines.append(ln)
    cleaned_lines = []
    prev_empty = False
    for ln in lines:
        is_empty = not ln.strip()
        if is_empty:
            if not prev_empty:
                cleaned_lines.append(ln)
            prev_empty = True
        else:
            cleaned_lines.append(ln)
            prev_empty = False
    raw_text = "\n".join(cleaned_lines).strip()
    text = cut_text_after_first_meli_link(raw_text)
    seen = set()
    urls: list[str] = []
    for u in hrefs:
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return text, urls

def cut_text_after_first_meli_link(text: str) -> str:
    from extractor import ML_SEC_RE
    if not text:
        return ""
    m = ML_SEC_RE.search(text)
    if not m:
        return text
    link_end = m.end(1)
    result = text[:link_end]
    lines = result.splitlines()
    clean_lines = []
    for ln in lines:
        ln_stripped = ln.strip()
        ln_lower = ln_stripped.lower()
        if (
            ln_lower.startswith("link do grupo")
            or ln_lower.startswith("☑️")
            or "link do grupo" in ln_lower
        ):
            break
        clean_lines.append(ln)
    return "\n".join(clean_lines).strip()

def compute_msg_id(text: str, urls: list[str]) -> str:
    combined = f"{text}||{'|'.join(urls)}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

async def has_image(bubble: Locator | None) -> bool:
    if bubble is None:
        return False
    img = bubble.locator("img[src^='blob:'], img[src^='data:'], div._1JVSX")
    count = await img.count()
    return count > 0

async def download_last_image(page: Page, download_dir: str, source_name: str = "") -> str | None:
    last = await get_last_message_bubble(page)
    if last is None:
        return None
    try:
        img_selectors = [
            "img[src^='blob:']",
            "img[src^='https://']",
            "img[data-plain-src]",
            "img[src*='mmg.whatsapp.net']",
            "img[src^='data:']",
        ]
        img_element = None
        img_url = None
        for selector in img_selectors:
            try:
                elem = last.locator(selector).first
                if await elem.count() > 0:
                    img_url = await elem.get_attribute("src")
                    if not img_url:
                        img_url = await elem.get_attribute("data-plain-src")
                    if img_url:
                        img_element = elem
                        print(f"   ✓ Imagem encontrada: {selector} ({img_url[:50]}...)")
                        break
            except Exception:
                continue
        if not img_element or not img_url:
            print("   ⚠️ Não encontrei imagem")
            return None
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        safe_source = re.sub(r'[^\w\-]', '_', source_name) if source_name else "unknown"
        timestamp = datetime.now().strftime("%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"img_{safe_source}_{timestamp}_{unique_id}.jpg"
        path = f"{download_dir}/{filename}"
        if img_url.startswith("blob:"):
            print(f"   → Convertendo blob em imagem real...")
            try:
                base64_data = await page.evaluate(
                    """
                    async (blobUrl) => {
                        const response = await fetch(blobUrl);
                        const blob = await response.blob();
                        return new Promise((resolve) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    }
                    """,
                    img_url
                )
                if base64_data and "base64," in base64_data:
                    base64_str = base64_data.split("base64,")[1]
                    image_bytes = base64.b64decode(base64_str)
                    with open(path, "wb") as f:
                        f.write(image_bytes)
                    print(f"   ✓ Imagem ORIGINAL do WhatsApp salva: {filename}")
                    return path
                else:
                    print("   ⚠️ Falha ao converter blob, usando screenshot...")
                    return await screenshot_last_image(page, download_dir, source_name)
            except Exception as e:
                print(f"   ⚠️ Erro ao converter blob ({e}), usando screenshot...")
                return await screenshot_last_image(page, download_dir, source_name)
        elif img_url.startswith("https://"):
            print(f"   → Baixando de URL: {img_url[:80]}...")
            response = await page.context.request.get(img_url)
            if response.status == 200:
                image_data = await response.body()
                with open(path, "wb") as f:
                    f.write(image_data)
                print(f"   ✓ Imagem baixada: {filename}")
                return path
            else:
                print(f"   ⚠️ Falha ao baixar (status {response.status})")
                return await screenshot_last_image(page, download_dir, source_name)
        else:
            print("   → Usando screenshot como fallback...")
            return await screenshot_last_image(page, download_dir, source_name)
    except Exception as e:
        print(f"   ⚠️ Erro geral ({e}), usando screenshot...")
        return await screenshot_last_image(page, download_dir, source_name)

async def screenshot_last_image(page: Page, download_dir: str, source_name: str = "") -> str | None:
    last = await get_last_message_bubble(page)
    if last is None:
        return None
    img = last.locator("img[src^='blob:'], img[src^='data:']").first
    try:
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        safe_source = re.sub(r'[^\w\-]', '_', source_name) if source_name else "unknown"
        timestamp = datetime.now().strftime("%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"screenshot_{safe_source}_{timestamp}_{unique_id}.jpg"
        path = f"{download_dir}/{filename}"
        await img.screenshot(path=path, type="jpeg", quality=90)
        print(f"   ✓ Screenshot salvo: {filename}")
        return path
    except Exception as e:
        print(f"   ⚠️ Erro ao tirar screenshot: {e}")
        return None