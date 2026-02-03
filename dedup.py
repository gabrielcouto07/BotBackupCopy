# dedup.py - Sistema de deduplicação para evitar reenvio do mesmo produto

import re
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from config import DEDUP_ENABLED, DEDUP_WINDOW_HOURS

logger = logging.getLogger("BotAfiliados")

DEDUP_CACHE_FILE = "dedup_cache.json"
MAX_CACHE_ENTRIES = 500

# Regex para extrair ASIN da Amazon
AMAZON_ASIN_RE = re.compile(
    r"(?:amazon\.[a-z.]+|amzn\.to)/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})",
    re.IGNORECASE,
)

AMAZON_ASIN_FALLBACK_RE = re.compile(
    r"/([A-Z0-9]{10})(?:[/?]|$)",
    re.IGNORECASE,
)

# Regex para extrair ID do Mercado Livre
ML_SEC_RE = re.compile(
    r"mercadolivre\.com(?:\.br)?/sec/([A-Za-z0-9]+)",
    re.IGNORECASE,
)

ML_PRODUCT_RE = re.compile(
    r"mercadolivre\.com(?:\.br)?/.*/p/(ML[A-Z][0-9]+)",
    re.IGNORECASE,
)


def _load_cache() -> dict:
    """Carrega cache do disco"""
    if not os.path.exists(DEDUP_CACHE_FILE):
        return {}
    
    try:
        with open(DEDUP_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar cache de dedup: {e}")
        return {}


def _save_cache(cache: dict):
    """Salva cache no disco, limitando tamanho máximo"""
    if len(cache) > MAX_CACHE_ENTRIES:
        sorted_items = sorted(cache.items(), key=lambda x: x[1])
        cache = dict(sorted_items[-MAX_CACHE_ENTRIES:])
        logger.info(f"🗑️ Dedup: Cache limitado a {MAX_CACHE_ENTRIES} entradas")
    
    try:
        with open(DEDUP_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"⚠️ Erro ao salvar cache de dedup: {e}")


def extract_product_id(url: str) -> Optional[str]:
    """Extrai o ID único do produto de uma URL (ASIN ou ID do ML)"""
    if not url:
        return None
    
    url_lower = url.lower()
    
    # Amazon
    if "amazon" in url_lower or "amzn.to" in url_lower:
        match = AMAZON_ASIN_RE.search(url)
        if match:
            return f"AMAZON:{match.group(1).upper()}"
        
        match = AMAZON_ASIN_FALLBACK_RE.search(url)
        if match:
            asin = match.group(1).upper()
            if len(asin) == 10 and asin.isalnum():
                return f"AMAZON:{asin}"
    
    # Mercado Livre
    if "mercadolivre" in url_lower:
        match = ML_SEC_RE.search(url)
        if match:
            return f"ML_SEC:{match.group(1)}"
        
        match = ML_PRODUCT_RE.search(url)
        if match:
            return f"ML:{match.group(1)}"
    
    return None


def extract_product_ids_from_urls(urls: list[str]) -> list[str]:
    """Extrai todos os IDs de produtos de uma lista de URLs"""
    product_ids = []
    seen = set()
    
    for url in urls:
        pid = extract_product_id(url)
        if pid and pid not in seen:
            seen.add(pid)
            product_ids.append(pid)
    
    return product_ids


def is_duplicate(target_group: str, text: str, urls: list[str]) -> bool:
    """Verifica se o produto já foi enviado recentemente"""
    if not DEDUP_ENABLED:
        return False
    
    product_ids = extract_product_ids_from_urls(urls)
    
    if not product_ids:
        return False
    
    cache = _load_cache()
    now = datetime.now()
    window = timedelta(hours=DEDUP_WINDOW_HOURS)
    
    for pid in product_ids:
        cache_key = f"{target_group}|{pid}"
        
        if cache_key in cache:
            sent_time_str = cache[cache_key]
            try:
                sent_time = datetime.fromisoformat(sent_time_str)
                time_diff = now - sent_time
                
                if time_diff < window:
                    remaining = window - time_diff
                    hours_remaining = remaining.total_seconds() / 3600
                    logger.info(f"   🚫 Produto {pid} já enviado há {time_diff.total_seconds()/60:.0f}min")
                    logger.info(f"   ⏰ Bloqueado por mais {hours_remaining:.1f}h")
                    return True
                else:
                    logger.info(f"   ✅ Produto {pid} - janela expirou")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao parsear timestamp: {e}")
    
    logger.info(f"   ✅ Produto(s) {product_ids} - OK para enviar")
    return False


def mark_as_sent(target_group: str, text: str, urls: list[str]):
    """Marca os produtos da mensagem como enviados"""
    if not DEDUP_ENABLED:
        return
    
    product_ids = extract_product_ids_from_urls(urls)
    
    if not product_ids:
        return
    
    cache = _load_cache()
    now = datetime.now().isoformat()
    
    for pid in product_ids:
        cache_key = f"{target_group}|{pid}"
        cache[cache_key] = now
        logger.info(f"   📝 Dedup: Marcado {pid} como enviado")
    
    _save_cache(cache)


def cleanup_expired_cache():
    """Remove entradas expiradas do cache"""
    if not DEDUP_ENABLED:
        return
    
    cache = _load_cache()
    now = datetime.now()
    window = timedelta(hours=DEDUP_WINDOW_HOURS)
    
    expired_keys = []
    
    for key, sent_time_str in cache.items():
        try:
            sent_time = datetime.fromisoformat(sent_time_str)
            if now - sent_time > window:
                expired_keys.append(key)
        except Exception:
            expired_keys.append(key)
    
    if expired_keys:
        for key in expired_keys:
            del cache[key]
        
        _save_cache(cache)
        logger.info(f"🗑️ Dedup: Removidas {len(expired_keys)} entradas expiradas")


def get_cache_stats() -> dict:
    """Retorna estatísticas do cache"""
    cache = _load_cache()
    
    stats = {
        "total_entries": len(cache),
        "by_group": {},
        "enabled": DEDUP_ENABLED,
        "window_hours": DEDUP_WINDOW_HOURS,
    }
    
    for key in cache:
        if "|" in key:
            group = key.split("|")[0]
            stats["by_group"][group] = stats["by_group"].get(group, 0) + 1
    
    return stats
