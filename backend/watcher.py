# watcher.py - Monitoramento e extração de mensagens do WhatsApp

import re
import hashlib
import base64
import uuid
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import Page, Locator


async def open_chat(page: Page, chat_name: str):
    """Abre um chat pelo nome, usando busca se necessário"""
    print(f"   🔎 Procurando chat: {chat_name}...")
    
    try:
        chat_locator = page.locator(f"span[title='{chat_name}']").first
        if await chat_locator.is_visible(timeout=2000):
            await chat_locator.click()
            await page.wait_for_timeout(500)
            return True
    except Exception:
        pass

    try:
        search_box = page.locator('div[contenteditable="true"][data-tab="3"]')
        await search_box.click()
        await page.wait_for_timeout(300)
        
        await search_box.press("Control+A")
        await search_box.press("Backspace")
        
        await search_box.fill(chat_name)
        await page.wait_for_timeout(2000)

        chat_locator = page.locator(f"span[title='{chat_name}']").first
        await chat_locator.click()

        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)
        return True

    except Exception as e:
        raise Exception(f"❌ Não foi possível encontrar o chat '{chat_name}'. Erro: {e}")


async def get_last_message_bubble(page: Page) -> Locator | None:
    """Retorna a última bolha de mensagem"""
    bubbles = page.locator("div.message-in, div.message-out")
    count = await bubbles.count()
    if count == 0:
        return None
    return bubbles.nth(count - 1)


async def extract_last_message_text_and_urls(page) -> tuple[str, list[str]]:
    """Extrai texto e URLs da última mensagem"""
    last = await get_last_message_bubble(page)
    if last is None:
        return "", []
    
    # Extrai links
    hrefs = []
    try:
        hrefs = await last.locator("a[href^='http']").evaluate_all(
            "els => els.map(a => a.getAttribute('href')).filter(Boolean)"
        )
        hrefs = [h.strip() for h in hrefs if isinstance(h, str) and h.strip()]
    except Exception:
        pass
    
    # Extrai texto
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
            raw_text = await last.inner_text(timeout=5000)
        except Exception:
            pass

    raw_text = (raw_text or "").strip()
    
    # Remove metadados (horário, encaminhado)
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
        
    # Remove linhas vazias duplicadas
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
    
    text = cut_text_after_link(raw_text)
    
    seen = set()
    urls: list[str] = []
    for u in hrefs:
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return text, urls


def cut_text_after_link(text: str) -> str:
    """Corta o texto após o link do ML ou Amazon"""
    if not text:
        return ""

    ml_re = re.compile(r"(mercadolivre\.com(?:\.br)?/.*?/sec/[A-Za-z0-9]+)", re.IGNORECASE)
    amz_re = re.compile(r"(https?://(?:www\.|m\.|smile\.)?amazon\.com\.br/[^\s]+|https?://amzn\.to/[^\s]+)", re.IGNORECASE)

    m_ml = ml_re.search(text)
    m_amz = amz_re.search(text)

    cut_index = len(text)
    found = False

    if m_ml:
        cut_index = min(cut_index, m_ml.end())
        found = True
    
    if m_amz:
        if m_amz.end() <= cut_index:
            cut_index = m_amz.end()
            found = True

    processed_text = text
    if found:
        processed_text = text[:cut_index]

    # Remove linhas de rodapé
    lines = processed_text.splitlines()
    clean_lines = []
    for ln in lines:
        ln_stripped = ln.strip()
        ln_lower = ln_stripped.lower()
        
        if (
            ln_lower.startswith("link do grupo")
            or ln_lower.startswith("☑️ link do grupo")
            or "link do grupo:" in ln_lower
            or ln_stripped == "☑️"
        ):
            break 
            
        clean_lines.append(ln)

    return "\n".join(clean_lines).strip()


def compute_msg_id(text: str, urls: list[str]) -> str:
    """Gera hash único para identificar a mensagem"""
    combined = f"{text}||{'|'.join(urls)}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


async def get_last_message_id(page: Page) -> str:
    """Obtém um ID estável da última mensagem pelo DOM (data-id/pre-plain-text)."""
    last = await get_last_message_bubble(page)
    if last is None:
        return ""
    try:
        msg_id = await last.get_attribute("data-id")
        if msg_id:
            return msg_id.strip()
        pre = await last.get_attribute("data-pre-plain-text")
        return (pre or "").strip()
    except Exception:
        return ""


async def has_image(bubble: Locator | None) -> bool:
    """Verifica se a bolha tem imagem"""
    if bubble is None:
        return False
    img = bubble.locator("img[src^='blob:'], img[src^='data:'], div._1JVSX")
    count = await img.count()
    return count > 0


async def download_last_image(page: Page, download_dir: str, source_name: str = "") -> str | None:
    """Baixa a imagem da última mensagem"""
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
                        print(f"   ✓ Imagem encontrada: {selector}")
                        break
            except Exception:
                continue
        
        if not img_element or not img_url:
            print("   ⚠️ Não encontrei imagem")
            return None
        
        # Aguarda imagem carregar
        print("   → Aguardando imagem carregar...")
        max_wait_attempts = 10
        for attempt in range(max_wait_attempts):
            try:
                is_loaded = await page.evaluate(
                    """
                    (img) => {
                        if (!img) return false;
                        if (img.naturalWidth > 50 && img.naturalHeight > 50) {
                            return true;
                        }
                        return false;
                    }
                    """,
                    await img_element.element_handle()
                )
                
                if is_loaded:
                    print(f"   ✓ Imagem carregada")
                    break
                else:
                    await page.wait_for_timeout(1000)
                    new_url = await img_element.get_attribute("src")
                    if new_url and new_url != img_url:
                        img_url = new_url
                        
            except Exception:
                await page.wait_for_timeout(1000)
        
        await page.wait_for_timeout(1500)
        
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        safe_source = re.sub(r'[^\w\-]', '_', source_name) if source_name else "unknown"
        timestamp = datetime.now().strftime("%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"img_{safe_source}_{timestamp}_{unique_id}.jpg"
        path = f"{download_dir}/{filename}"

        if img_url.startswith("blob:"):
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
                    print(f"   ✓ Imagem salva: {filename}")
                    return path
                else:
                    return await screenshot_last_image(page, download_dir, source_name)
            except Exception:
                return await screenshot_last_image(page, download_dir, source_name)
        elif img_url.startswith("https://"):
            response = await page.context.request.get(img_url)
            if response.status == 200:
                image_data = await response.body()
                with open(path, "wb") as f:
                    f.write(image_data)
                return path
            else:
                return await screenshot_last_image(page, download_dir, source_name)
        else:
            return await screenshot_last_image(page, download_dir, source_name)
    except Exception:
        return await screenshot_last_image(page, download_dir, source_name)


async def screenshot_last_image(page: Page, download_dir: str, source_name: str = "") -> str | None:
    """Fallback: tira screenshot da imagem se download falhar"""
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
