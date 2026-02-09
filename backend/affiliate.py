# affiliate.py - Geração de links afiliados (Mercado Livre e Amazon)

import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from playwright.async_api import TimeoutError as PWTimeout

# API do Mercado Livre
API_CREATE_LINK = "https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links"

ML_SEC_RE = re.compile(
    r"https?://[\w.-]*mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+",
    re.IGNORECASE,
)

# Cache de CSRF
_CACHED_CSRF: str | None = None
_CSRF_LOCK = asyncio.Lock()

# Regex para ASIN da Amazon
ASIN_RE_LIST = [
    re.compile(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/product/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/ASIN/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
    re.compile(r"/exec/obidos/ASIN/([A-Z0-9]{10})(?:[/?]|$)", re.IGNORECASE),
]

AMAZON_RE = re.compile(
    r"https?://(?:(?:www|m|smile)\.)?(?:amazon\.[a-z.]{2,}|amzn\.to)/[^\s]+",
    re.IGNORECASE,
)

AMZN_SHORT_RE = re.compile(r"https?://(?:amzn\.to)/", re.IGNORECASE)


def _is_sec(url: str) -> bool:
    return bool(ML_SEC_RE.search((url or "").strip()))


def _is_product_page(url: str) -> bool:
    url_lower = (url or "").lower()
    has_mlb = bool(re.search(r"mlb\d+", url_lower, re.IGNORECASE))
    is_not_sec = "/sec/" not in url_lower
    is_not_review = "/social/" not in url_lower and "/minutoreview" not in url_lower
    return has_mlb and is_not_sec and is_not_review


async def _click_ir_para_produto(page) -> bool:
    """Clica no botão 'Ir para produto' em páginas minutoreview"""
    candidates = [
        page.get_by_role("button", name="Ir para produto").first,
        page.get_by_role("link", name="Ir para produto").first,
        page.locator("a:has-text('Ir para produto')").first,
        page.locator("button:has-text('Ir para produto')").first,
        page.locator("text=Ir para produto").first,
        page.get_by_text("Ir para produto", exact=False).first,
    ]

    for loc in candidates:
        try:
            if await loc.count() == 0:
                continue
            await loc.scroll_into_view_if_needed(timeout=2000)
            await loc.click(timeout=8000)
            return True
        except Exception:
            continue

    return False


async def _ensure_csrf_token_from_affiliates(page) -> str | None:
    """Captura token CSRF da página de afiliados"""
    global _CACHED_CSRF

    async with _CSRF_LOCK:
        if _CACHED_CSRF:
            return _CACHED_CSRF

        try:
            print(" → Navegando para página de afiliados ML...")

            await page.goto(
                "https://www.mercadolivre.com.br/afiliados",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await page.wait_for_timeout(2000)

            token = await page.evaluate(
                """
                () => {
                    const m =
                        document.querySelector('meta[name="csrf-token"]') ||
                        document.querySelector('meta[name="csrf_token"]') ||
                        document.querySelector('meta[name="csrfToken"]');
                    return m ? (m.content || '') : '';
                }
                """
            )

            token = (token or "").strip()

            if token:
                _CACHED_CSRF = token
                print(f" ✓ CSRF capturado: {token[:20]}...")
                return token

            print(" ⚠️ CSRF não encontrado")
            return None

        except Exception as e:
            print(f" ✗ Erro ao capturar CSRF: {e}")
            return None


async def _resolve_product_url(page, sec_url: str) -> str | None:
    """Resolve link /sec/ para URL do produto"""
    try:
        print(f" → Abrindo: {sec_url[:80]}...")

        await page.goto(sec_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)

        url_inicial = page.url

        if _is_product_page(url_inicial):
            print(" ✓ Já está na página do produto!")
            return url_inicial

        if "/social/" in url_inicial.lower() or "/minutoreview" in url_inicial.lower():
            print(" → Detectado minutoreview, clicando 'Ir para produto'...")

            clicked = await _click_ir_para_produto(page)

            if not clicked:
                print(" ⚠️ Botão 'Ir para produto' não encontrado")
                return None

            print(" ✓ Clicou em 'Ir para produto'")

            try:
                await page.wait_for_load_state("domcontentloaded", timeout=30000)
            except Exception:
                pass

            await page.wait_for_timeout(2000)

        url_final = page.url

        if "MLB" in url_final.upper():
            print(" ✓ URL de produto válida")
            return url_final
        else:
            print(" ⚠️ URL não parece ser de produto")
            return None

    except Exception as e:
        print(f" ✗ Erro ao resolver URL: {e}")

        try:
            current = page.url
            if "MLB" in current.upper() and "/sec/" not in current.lower():
                return current
        except Exception:
            pass

        return None


async def _create_sec_via_api(page, product_url: str, tag: str) -> str | None:
    """Gera link /sec/ via API do Mercado Livre"""
    csrf = await _ensure_csrf_token_from_affiliates(page)

    if not csrf:
        print(" ✗ Não consegui obter CSRF")
        return None

    headers = {
        "x-csrf-token": csrf,
        "referer": "https://www.mercadolivre.com.br/afiliados",
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://www.mercadolivre.com.br",
    }

    payload = {"url": product_url, "tag": tag}

    print(" → Chamando API de afiliados ML...")

    try:
        resp = await page.context.request.post(
            API_CREATE_LINK,
            data=json.dumps(payload),
            headers=headers,
            timeout=60000,
        )

    except Exception as e:
        print(f" ✗ Falha ao chamar API: {e}")
        return None

    if resp.status not in (200, 201):
        try:
            body = await resp.text()
        except Exception:
            body = ""

        print(f" ✗ API retornou {resp.status}")

        global _CACHED_CSRF
        if resp.status in (401, 403):
            async with _CSRF_LOCK:
                _CACHED_CSRF = None

        return None

    try:
        data = await resp.json()
    except Exception:
        try:
            data = {"_raw": await resp.text()}
        except Exception:
            data = {}

    sec_id = (data.get("id") or "").strip()

    if not sec_id:
        maybe_url = data.get("url") or data.get("link") or ""
        if isinstance(maybe_url, str) and "/sec/" in maybe_url:
            return maybe_url.strip()
        print(f" ✗ Resposta inesperada da API")
        return None

    new_sec = f"https://mercadolivre.com/sec/{sec_id}"
    print(f" ✓ Link gerado: {sec_id}")

    return new_sec


def _extract_asin_from_url(u: str) -> str | None:
    if not u:
        return None
    for rgx in ASIN_RE_LIST:
        m = rgx.search(u)
        if m:
            return m.group(1).upper()
    return None


async def _extract_asin_from_page_dom(page) -> str | None:
    """Extrai ASIN do HTML quando não está na URL"""
    try:
        asin = await page.evaluate(
            """
            () => {
              const i = document.querySelector('input#ASIN, input[name="ASIN"]');
              if (i && i.value && i.value.length === 10) return i.value;

              const el = document.querySelector('[data-asin]');
              if (el && el.getAttribute('data-asin') && el.getAttribute('data-asin').length === 10)
                return el.getAttribute('data-asin');

              const meta = document.querySelector('meta[name="ASIN"]');
              if (meta && meta.content && meta.content.length === 10) return meta.content;

              const html = document.documentElement ? document.documentElement.innerHTML : '';
              const m = html.match(/"ASIN"\\s*:\\s*"([A-Z0-9]{10})"/i);
              return m ? m[1] : null;
            }
            """
        )
        if asin and isinstance(asin, str) and len(asin) == 10:
            return asin.upper()
    except Exception:
        pass
    return None


def _build_canonical_amazon_url(netloc: str, asin: str, tag: str) -> str:
    base = f"https://{netloc}/dp/{asin}/"
    return f"{base}?{urlencode({'tag': tag})}"


def _fallback_replace_tag(original_url: str, tag: str) -> str:
    """Substitui/adiciona tag na URL quando não acha ASIN"""
    parsed = urlparse(original_url)
    q = parse_qs(parsed.query)
    q["tag"] = [tag]
    for k in ["ref", "ref_", "pf_rd_r", "pf_rd_p", "pd_rd_r", "pd_rd_w", "qid", "sr", "sprefix", "keywords"]:
        q.pop(k, None)
    new_query = urlencode(q, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


async def generate_affiliate_link(
    page_m, any_url: str, tag: str, max_retries: int = 2
) -> tuple[str | None, str | None]:
    """Gera link afiliado do Mercado Livre"""
    any_url = (any_url or "").strip()
    if not any_url:
        return None, None

    tag = (tag or "").strip()
    if not tag:
        print(" ✗ Tag do afiliado ML vazia")
        return None, None

    for attempt in range(max_retries):
        try:
            print(f"\n 🔄 [ML] Gerando link (tentativa {attempt+1}/{max_retries})")

            product_url = await _resolve_product_url(page_m, any_url)

            if not product_url:
                print(" ✗ Não consegui chegar na página do produto")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                    continue
                return None, None

            sec = await _create_sec_via_api(page_m, product_url, tag)

            if sec:
                print(f" ✅ Link afiliado ML gerado: {sec}")

                try:
                    await page_m.goto(product_url, wait_until="domcontentloaded", timeout=30000)
                    await page_m.wait_for_timeout(1500)
                except Exception:
                    pass

                return sec, product_url

            else:
                print(" ✗ API não conseguiu gerar link")

                if attempt < max_retries - 1:
                    global _CACHED_CSRF
                    async with _CSRF_LOCK:
                        _CACHED_CSRF = None
                    await asyncio.sleep(3)
                    continue

        except Exception as e:
            print(f" ✗ Erro na tentativa {attempt+1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
                continue

    return None, None


async def generate_amazon_affiliate_link_async(
    page_m, original_url: str, tag: str
) -> tuple[str | None, str | None]:
    """Gera link afiliado da Amazon"""
    original_url = (original_url or "").strip()
    tag = (tag or "").strip()

    if not original_url or not tag:
        return None, None

    print(f"\n 🔄 [AMAZON] Processando URL...")

    asin = _extract_asin_from_url(original_url)
    parsed = urlparse(original_url)
    netloc = parsed.netloc or "www.amazon.com.br"

    resolved_url = original_url
    if AMZN_SHORT_RE.search(original_url) or not asin:
        try:
            print(f" → Resolvendo redirect...")
            await page_m.goto(original_url, wait_until="domcontentloaded", timeout=60000)
            await page_m.wait_for_timeout(1500)

            resolved_url = page_m.url

            asin = _extract_asin_from_url(resolved_url)
            if not asin:
                asin = await _extract_asin_from_page_dom(page_m)

            p2 = urlparse(resolved_url)
            if p2.netloc:
                netloc = p2.netloc

        except Exception as e:
            print(f" ⚠️ Falha ao resolver: {e}")

    if asin:
        affiliate = _build_canonical_amazon_url(netloc, asin, tag)
        print(f" ✅ [AMAZON] ASIN={asin}")
        return affiliate, resolved_url

    try:
        affiliate = _fallback_replace_tag(resolved_url, tag)
        print(f" ⚠️ [AMAZON] Sem ASIN, usando fallback")
        return affiliate, resolved_url
    except Exception as e:
        print(f" ✗ [AMAZON] Falha total: {e}")
        return None, resolved_url


async def download_product_image(
    page, product_url: str, out_dir: str = "./tmp"
) -> str | None:
    """Baixa imagem do produto (ML ou Amazon)"""
    try:
        print(" → Baixando imagem do produto...")

        current = page.url
        if product_url.split("?")[0] not in current:
            try:
                await page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

        img_selectors = [
            "figure.ui-pdp-gallery__figure img[src^='http']",
            "img.ui-pdp-image[src^='http']",
            "div.ui-pdp-gallery img[src^='http']",
            "img[src*='mlb-s1']",
            "img[src*='mlb-s2']",
            "img[src*='mlb-s3']",
            "#landingImage",
            "#imgBlkFront",
            "#ebooksImgBlkFront",
            "#main-image",
            "img[data-a-image-name='landingImage']",
            "#kby-start-reading-image",
        ]

        img_element = None

        for selector in img_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.count() > 0 and await elem.is_visible():
                    img_element = elem
                    print(f" ✓ Imagem encontrada")
                    break
            except Exception:
                continue

        if not img_element:
            print(" ✗ Não encontrei imagem")
            return None

        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir) / "product_image.jpg"

        await img_element.screenshot(
            path=str(out_path),
            type="jpeg",
            quality=90,
            timeout=15000,
        )

        print(f" ✓ Imagem salva")
        return str(out_path)

    except Exception as e:
        print(f" ✗ Erro ao baixar imagem: {e}")
        return None
