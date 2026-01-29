import os

CHROME_USER_DATA_DIR = "C:\\BotChromeProfile"
CHROME_PROFILE_DIR_NAME = "Default"
HEADLESS = False

DOWNLOAD_DIR = "./tmp"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MELI_AFFILIATE_TAG = "arthurothero"
AMAZON_AFFILIATE_TAG = "seunome-20"

AMAZON_ENABLED = True # Set False para desabilitar Amazon 

SUPERHERO_EMOJI = "🦸"

GATILHOS = [
    "⚡ CORRE!",
    "🔥 OFERTA IMPERDÍVEL!",
    "💰 PREÇO NUNCA VISTO!",
    "⏰ ÚLTIMAS UNIDADES!",
    "🎯 NESSE PREÇO NUNCA!",
    "💥 ACABANDO!",
    "😱 ERRO DE PREÇO?",
    "🎯 NESSE PREÇO NUNCA!",
    "💰 PREÇO NUNCA VISTO!",
]

GATILHO_CHANCE = 0.20

BUBBLE_REFRESH_DELAY = 2

POLL_SECONDS = 180

RESTART_EVERY_CYCLES = 40

CYCLE_TIMEOUT_SECONDS = 240

SLEEP_GRANULARITY_SECONDS = 60

NIGHT_MODE_ENABLED = True
NIGHT_START_HOUR = 1
NIGHT_END_HOUR = 8

CHANNEL_PAIRS = [
    ("Testes", "Flash Promos 🛒⚡", "Testes"),
    ("Herói da Promo #729", "Flash Promos 🛒⚡", "Herói da Promo"),
    ("Home Deals [12]", "Flash Promos 🛒⚡", "Home Deals"),
    ("Tech Deals 🎯 [01]", "Flash Promos 🛒⚡", "Tech Deals"),
    ("Guerra Deals Fit [112]", "Flash Promos 🛒⚡", "Guerra Deals"),
]

GROUP_LINKS = {
    "Flash Promos 🛒⚡": "https://chat.whatsapp.com/BjtCMWHoboY7XWkB6WOOJ7",
}