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

NIGHT_MODE_ENABLED = True
NIGHT_START_HOUR = 1
NIGHT_END_HOUR = 8

CHANNEL_PAIRS = [
    ("Herói da Promo #731", "Super Promos", "Herói da Promo"),
    ("Home Deals [12]", "Super Promos", "Home Deals"),
    ("Tech Deals 🎯 [20]", "Super Promos", "Tech Deals"),
]

GROUP_LINKS = {
    "Super Promos": "https://chat.whatsapp.com/GCLg0s12zFqDJvC51o5V5X",
}