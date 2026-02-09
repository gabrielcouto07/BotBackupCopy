# config.py - Configurações do Bot
# Carrega configurações do settings.json (editável via frontend)

import os
import json
from pathlib import Path

# Caminho do arquivo de configurações
SETTINGS_FILE = Path(__file__).parent / "settings.json"


def load_settings() -> dict:
    """Carrega configurações do arquivo JSON"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_settings(settings: dict):
    """Salva configurações no arquivo JSON"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def reload_config():
    """Recarrega todas as variáveis globais do settings.json"""
    global MELI_AFFILIATE_TAG, AMAZON_AFFILIATE_TAG, AMAZON_ENABLED
    global FACEBOOK_ENABLED, FACEBOOK_PAGE_URL, FACEBOOK_POST_INTERVAL
    global GROUP_LINK, CHANNEL_PAIRS
    global POLL_SECONDS, DEDUP_WINDOW_HOURS
    global NIGHT_MODE_ENABLED, NIGHT_START_HOUR, NIGHT_END_HOUR
    global GATILHOS, GATILHO_CHANCE, GATILHO_ENABLED

    settings = load_settings()

    # Affiliate
    affiliate = settings.get("affiliate", {})
    MELI_AFFILIATE_TAG = affiliate.get("meli_tag", "")
    AMAZON_AFFILIATE_TAG = affiliate.get("amazon_tag", "")
    AMAZON_ENABLED = affiliate.get("amazon_enabled", True)

    # Facebook
    fb = settings.get("facebook", {})
    FACEBOOK_ENABLED = fb.get("enabled", False)
    FACEBOOK_PAGE_URL = fb.get("page_url", "")
    FACEBOOK_POST_INTERVAL = fb.get("post_interval_minutes", 30) * 60

    # WhatsApp
    wpp = settings.get("whatsapp", {})
    GROUP_LINK = " " + wpp.get("group_link", "").strip()

    # Channel Pairs (only enabled ones)
    pairs = settings.get("channel_pairs", [])
    CHANNEL_PAIRS = [
        (p["source"], p["target"], p["description"])
        for p in pairs if p.get("enabled", True)
    ]

    # Timing
    timing = settings.get("timing", {})
    POLL_SECONDS = timing.get("poll_seconds", 180)
    DEDUP_WINDOW_HOURS = timing.get("dedup_window_hours", 3)
    NIGHT_MODE_ENABLED = timing.get("night_mode_enabled", True)
    NIGHT_START_HOUR = timing.get("night_start_hour", 1)
    NIGHT_END_HOUR = timing.get("night_end_hour", 8)

    # Triggers
    triggers = settings.get("triggers", {})
    GATILHO_ENABLED = triggers.get("enabled", True)
    GATILHO_CHANCE = triggers.get("chance", 0.20)
    GATILHOS = triggers.get("list", [])


# ============================================================
# Configurações fixas (não editáveis via frontend)
# ============================================================

# Navegador Chrome
CHROME_USER_DATA_DIR = "C:\\BotChromeProfile"
CHROME_PROFILE_DIR_NAME = "Default"
HEADLESS = True

# Pasta temporária para imagens
DOWNLOAD_DIR = "./tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Emoji removido das mensagens
SUPERHERO_EMOJI = "🦸"

# Delays e timings fixos
BUBBLE_REFRESH_DELAY = 2
RESTART_EVERY_CYCLES = 25
CYCLE_TIMEOUT_SECONDS = 300
SLEEP_GRANULARITY_SECONDS = 60
LOG_CLEANUP_CYCLES = 50
FACEBOOK_POST_TIMEOUT = 120
DEDUP_ENABLED = True

# ============================================================
# Variáveis dinâmicas (carregadas do settings.json)
# ============================================================

MELI_AFFILIATE_TAG = ""
AMAZON_AFFILIATE_TAG = ""
AMAZON_ENABLED = True
FACEBOOK_ENABLED = False
FACEBOOK_PAGE_URL = ""
FACEBOOK_POST_INTERVAL = 1800
GROUP_LINK = ""
CHANNEL_PAIRS = []
POLL_SECONDS = 180
DEDUP_WINDOW_HOURS = 3
NIGHT_MODE_ENABLED = True
NIGHT_START_HOUR = 1
NIGHT_END_HOUR = 8
GATILHOS = []
GATILHO_CHANCE = 0.20
GATILHO_ENABLED = True

# Carrega configurações na inicialização
reload_config()
