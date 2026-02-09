# extractor.py - Processamento de texto e URLs

import re

# Regex para URLs
ML_SEC_RE = re.compile(
    r"(https?://[\w.-]*mercadolivre\.com(?:\.br)?/sec/[A-Za-z0-9]+)",
    re.IGNORECASE,
)

AMAZON_RE = re.compile(
    r"https?://(?:(?:www|m|smile)\.)?(?:amazon\.[a-z.]{2,}|amzn\.to)/[^\s]+",
    re.IGNORECASE,
)

URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)


def remove_text_formatting(text: str) -> str:
    """Remove formatações do WhatsApp: *negrito*, _itálico_, ~cortado~, `código`"""
    if not text:
        return ""
    
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'~([^~]+)~', r'\1', text)
    text = re.sub(r'```([^`]*)```', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    return text


def cut_text_after_first_meli_link(text: str) -> str:
    """Corta o texto após o link do Mercado Livre"""
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


def extract_urls_from_text(text: str) -> list[str]:
    """Extrai todas URLs do texto"""
    if not text:
        return []
    
    urls = URL_RE.findall(text)
    cleaned: list[str] = []
    
    for u in urls:
        u2 = u.rstrip(".,;:!?)]'\\'\"")
        cleaned.append(u2)
    
    seen = set()
    out: list[str] = []
    
    for u in cleaned:
        if u not in seen:
            seen.add(u)
            out.append(u)
    
    return out


def filter_meli_sec_urls(urls: list[str]) -> list[str]:
    """Filtra apenas URLs do Mercado Livre /sec/"""
    if not urls:
        return []
    
    return [url for url in urls if ML_SEC_RE.match(url)]


def replace_urls_in_text(text: str, mapping: dict[str, str]) -> str:
    """Substitui URLs antigas por afiliadas"""
    if not text or not mapping:
        return text or ""
    
    result = text
    for old_url, new_url in mapping.items():
        result = result.replace(old_url, new_url)
    
    return result


def process_text_enhancements(text: str) -> str:
    """Processa texto para melhorias visuais"""
    if not text:
        return text
    return text


def format_old_price_with_strikethrough(text: str) -> str:
    """Adiciona ~riscado~ no preço antigo para WhatsApp"""
    if not text:
        return text
    
    price_pattern = r'(R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    
    text = re.sub(
        r'(\b[Dd]e:?\s*)' + price_pattern,
        r'\1~\2~',
        text
    )
    
    text = re.sub(
        price_pattern + r'(\s+[Pp]or\s+)' + price_pattern,
        r'~\1~\2\3',
        text
    )
    
    return text


def filter_amazon_urls(urls: list[str]) -> list[str]:
    """Filtra apenas URLs da Amazon"""
    if not urls:
        return []
    
    return [url for url in urls if AMAZON_RE.match(url)]
