import os

CHROME_USER_DATA_DIR = "C:\\BotChromeProfile"
CHROME_PROFILE_DIR_NAME = "Default"
HEADLESS = True

DOWNLOAD_DIR = "./tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MELI_AFFILIATE_TAG = "silvagabriel20230920180155"

SUPERHERO_EMOJI = "🦸"

GATILHOS = [
    "⚡ CORRE!",
    "🔥 OFERTA IMPERDÍVEL!",
    "💰 PREÇO NUNCA VISTO!",
    "⏰ ÚLTIMAS UNIDADES!",
    "🎯 NESSE PREÇO NUNCA!",
    "💥 ACABANDO!",
]
GATILHO_CHANCE = 0.20

BUBBLE_REFRESH_DELAY = 2

POLL_SECONDS = 180

RESTART_EVERY_CYCLES = 40

CYCLE_TIMEOUT_SECONDS = 240

SLEEP_GRANULARITY_SECONDS = 5

NIGHT_MODE_ENABLED = True
NIGHT_START_HOUR = 21
NIGHT_END_HOUR = 9

CHANNEL_PAIRS = [
    ("Tech Deals 🎯 [01]", "Promo Codes [10] - Promoções e Cupons", ""),
    ("Home Deals [12]", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Rafa Shop", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Parfum Deals 👔 [11]", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Guerra Deals Fit [112]", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Tech Promos", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Guerra Deals Fit [73]", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
    ("Super Promos [21]", "Promo Codes [10] - Promoções e Cupons", "Teste de Funcionalidades"),
]

GROUP_LINKS = {
    "Promo Codes [10] - Promoções e Cupons": "https://chat.whatsapp.com/GCLG0St2zFqDJvC51o5V5X",
}