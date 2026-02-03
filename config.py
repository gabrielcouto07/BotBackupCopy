# config.py - Configurações do Bot

import os

# Navegador Chrome
CHROME_USER_DATA_DIR = "C:\\BotChromeProfile"
CHROME_PROFILE_DIR_NAME = "Default"
HEADLESS = False

# Pasta temporária para imagens
DOWNLOAD_DIR = "./tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Tags de afiliados
MELI_AFFILIATE_TAG = "silvagabriel20230920180155"
AMAZON_AFFILIATE_TAG = "superprom03bb-20"
AMAZON_ENABLED = True

# Facebook
FACEBOOK_ENABLED = True
FACEBOOK_PAGE_URL = "https://www.facebook.com/profile.php?id=61587267939249"
FACEBOOK_POST_INTERVAL = 1800  # 30 minutos

# Emoji removido das mensagens
SUPERHERO_EMOJI = "🦸"

# Gatilhos adicionados aleatoriamente
GATILHOS = [
    "⚡ CORRE!",
    "🔥 OFERTA IMPERDÍVEL!",
    "💰 PREÇO NUNCA VISTO!",
    "⏰ ÚLTIMAS UNIDADES!",
    "🎯 NESSE PREÇO NUNCA!",
    "💥 ACABANDO!",
]
GATILHO_CHANCE = 0.20  # 20% de chance

# Delays e timings
BUBBLE_REFRESH_DELAY = 2
POLL_SECONDS = 180  # 3 minutos entre ciclos
RESTART_EVERY_CYCLES = 25
CYCLE_TIMEOUT_SECONDS = 240
SLEEP_GRANULARITY_SECONDS = 60
LOG_CLEANUP_CYCLES = 50

# Deduplicação (evita reenvio do mesmo produto)
DEDUP_ENABLED = True
DEDUP_WINDOW_HOURS = 3

# Modo noturno (pausa durante a madrugada)
NIGHT_MODE_ENABLED = True
NIGHT_START_HOUR = 1
NIGHT_END_HOUR = 8

# Grupos WhatsApp: (source, target, descrição)
CHANNEL_PAIRS = [
    ("Herói da Promo #731", "Super Promos [21]", "Herói da Promo"),
    ("Home Deals [12]", "Super Promos [21]", "Home Deals"),
    ("Tech Deals 🎯 [20]", "Super Promos [21]", "Tech Deals"),
    ("Parfum Deals 👔 [15]", "Super Promos [21]", "Parfum Deals"),
]

# Link do grupo WhatsApp (adicionado no fim das mensagens)
GROUP_LINK = "https://chat.whatsapp.com/GCLg0s12zFqDJvC51o5V5X"
