import asyncio
import traceback
import random
import os
import logging
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from config import (
    BUBBLE_REFRESH_DELAY,
    CHANNEL_PAIRS,
    DOWNLOAD_DIR,
    MELI_AFFILIATE_TAG,
    CHROME_USER_DATA_DIR,
    CHROME_PROFILE_DIR_NAME,
    HEADLESS,
    SUPERHERO_EMOJI,
    GATILHOS,
    GATILHO_CHANCE,
    POLL_SECONDS,
    RESTART_EVERY_CYCLES,
    CYCLE_TIMEOUT_SECONDS,
    SLEEP_GRANULARITY_SECONDS,
    NIGHT_MODE_ENABLED,
    NIGHT_START_HOUR,
    NIGHT_END_HOUR,
)
from watcher import (
    open_chat,
    extract_last_message_text_and_urls,
    compute_msg_id,
    get_last_message_bubble,
    has_image,
    download_last_image,
)
from extractor import (
    extract_urls_from_text,
    replace_urls_in_text,
    format_old_price_with_strikethrough,
)
from affiliate import generate_affiliate_link
from sender_whatsapp import send_image_with_caption
from storage import get_last_seen as load_last_seen, save_last_seen


def setup_logger():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = logging.getLogger("BotAfiliados")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.info(f"✅ Sistema de logs iniciado: {log_file}")
    return logger


logger = setup_logger()


class RestartRequested(Exception):
    """Raised to force a clean browser/context restart."""


async def chunked_sleep(total_seconds: int, chunk_seconds: int, *, label: str = ""):
    remaining = max(0, int(total_seconds))
    chunk = max(1, int(chunk_seconds))
    while remaining > 0:
        step = min(chunk, remaining)
        await asyncio.sleep(step)
        remaining -= step
        if remaining > 0 and label:
            logger.info(f"   ⏳ {label}: {remaining}s restantes...")


async def ensure_whatsapp_ready(page_w):
    """Light health-check. If WA is not usable, try reload, else request restart."""
    try:
        await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=15000)
        return
    except Exception:
        logger.warning("⚠️  WhatsApp parece travado/fora do ar. Tentando recarregar...")

    try:
        await page_w.reload(wait_until="domcontentloaded", timeout=60000)
        await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=60000)
        logger.info("✅ WhatsApp voltou após reload")
    except Exception as e:
        logger.error(f"❌ WhatsApp não voltou após reload: {e}")
        raise RestartRequested("WhatsApp not ready")


def process_text_enhancements(text: str) -> str:
    """
    Remove emoji específico (🦸) mas MANTÉM formatação, quebras de linha e emojis
    """
    if not text:
        return text

    original_len = len(text)

    text = re.sub(r"🦸[\u200d\ufe0f♂️♀️🏻-🏿]*", "", text)
    text = re.sub(r"[\u200d\ufe0f🏻-🏿]+", "", text)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        cleaned_line = " ".join(line.split())
        cleaned_lines.append(cleaned_line)

    text = "\n".join(cleaned_lines)

    if len(text) < original_len:
        logger.info(f"   🧹 Removido emoji: {SUPERHERO_EMOJI}")

    if random.random() < GATILHO_CHANCE:
        gatilho = random.choice(GATILHOS)
        text = f"{gatilho}\n\n{text}"
        logger.info(f"   ✨ Gatilho adicionado: {gatilho}")

    return text


def filter_meli_sec_urls(urls: list[str]) -> list[str]:
    if not urls:
        return []
    meli_sec_pattern = re.compile(r"mercadolivre\..*?/sec/", re.IGNORECASE)
    return [u for u in urls if u and meli_sec_pattern.search(u)]


def cleanup_temp_images(download_dir: str):
    try:
        temp_dir = Path(download_dir)
        if not temp_dir.exists():
            return
        for img_file in temp_dir.glob("*.jpg"):
            try:
                img_file.unlink()
            except Exception:
                pass
        logger.info("🗑️  Cleanup: imagens temporárias deletadas")
    except Exception as e:
        logger.warning(f"⚠️  Erro ao limpar imagens: {e}")


async def wait_for_day_time():
    if not NIGHT_MODE_ENABLED:
        return
    now = datetime.now()
    current_hour = now.hour
    if NIGHT_START_HOUR <= current_hour < NIGHT_END_HOUR or (
        NIGHT_START_HOUR > NIGHT_END_HOUR
        and (current_hour >= NIGHT_START_HOUR or current_hour < NIGHT_END_HOUR)
    ):
        logger.info(f"😴 Modo noturno ativo ({NIGHT_START_HOUR:02d}:00-{NIGHT_END_HOUR:02d}:00)")
        logger.info(f"   ⏸️  Pausando até {NIGHT_END_HOUR:02d}:00...")
        while True:
            now = datetime.now()
            current_hour = now.hour
            if not (
                NIGHT_START_HOUR <= current_hour < NIGHT_END_HOUR
                or (
                    NIGHT_START_HOUR > NIGHT_END_HOUR
                    and (current_hour >= NIGHT_START_HOUR or current_hour < NIGHT_END_HOUR)
                )
            ):
                logger.info("☀️  Modo diurno - retomando operação")
                break
            await asyncio.sleep(300)


async def process_new_message(
    page_w,
    page_m,
    text: str,
    hrefs: list[str],
    source_name: str,
    target_name: str,
    description: str,
) -> bool:
    bubble = await get_last_message_bubble(page_w)
    if not await has_image(bubble):
        logger.warning(f"   ⚠️  {source_name}: Sem IMAGEM - IGNORANDO mensagem")
        return True

    logger.info(f"   📸 {source_name}: Mensagem tem IMAGEM ✅")

    urls = hrefs if hrefs else []
    if not urls:
        urls = extract_urls_from_text(text)

    meli_urls = filter_meli_sec_urls(urls)
    if not meli_urls:
        logger.warning(f"   ⚠️  {source_name}: Sem link /sec/ ML - IGNORANDO")
        return True

    mapping = {}
    for u in meli_urls[:3]:
        logger.info(f"   🔗 Gerando afiliado para: {u[:60]}...")
        new_u, prod_url = await generate_affiliate_link(page_m, u, MELI_AFFILIATE_TAG)
        if new_u:
            mapping[u] = new_u
            logger.info(f"   ✅ Gerado: {new_u[:60]}...")
            break

    if not mapping:
        logger.error(f"   ❌ {source_name}: Falha ao gerar afiliado")
        return False

    enhanced_text = process_text_enhancements(text)
    new_text = replace_urls_in_text(enhanced_text, mapping)
    new_text = format_old_price_with_strikethrough(new_text)
    final_text = new_text

    logger.info(f"   📝 Texto processado: {len(final_text)} chars")
    preview = final_text.replace("\n", " ")[:80]
    logger.info(f"   📝 Preview: {preview}...")
    logger.info(f"   📸 Baixando imagem original do WhatsApp...")

    img_path = await download_last_image(page_w, DOWNLOAD_DIR, source_name)
    if not img_path:
        logger.error(f"   ❌ {source_name}: FALHA ao capturar/baixar imagem")
        return False

    logger.info(f"   ✅ Imagem pronta: {os.path.basename(img_path)}")

    await page_w.bring_to_front()
    await page_w.wait_for_timeout(300)

    logger.info(f"   📤 {source_name}: Enviando IMAGEM + LEGENDA para {target_name}...")
    ok = await send_image_with_caption(
        page_w,
        target_name,
        img_path,
        final_text,
        target_group=target_name,
    )

    if img_path and os.path.exists(img_path):
        try:
            os.remove(img_path)
            logger.info(f"   🗑️  Imagem temporária deletada")
        except Exception as e:
            logger.warning(f"   ⚠️  Erro ao deletar imagem: {e}")

    if ok:
        logger.info(f"   ✅✅✅ {source_name}: SUCESSO!")
    else:
        logger.error(f"   ❌ {source_name}: FALHA ao enviar")

    return ok


async def monitoring_loop(page_w, page_m):
    last_seen_dict = {}
    logger.info("")
    logger.info("=" * 80)
    logger.info("🤖 BOT INICIADO - 3 Sources → 1 Target (Super Promos)")
    logger.info("=" * 80)
    logger.info("")
    for source_group, target_group, description in CHANNEL_PAIRS:
        last_seen_dict[source_group] = load_last_seen(source_group)
        logger.info(f"📋 {description}")
        logger.info(f"   Source: {source_group}")
        logger.info(f"   Target: {target_group}")
        if last_seen_dict[source_group]:
            logger.info(f"   Último ID: {last_seen_dict[source_group][:16]}...")
        else:
            logger.info(f"   Último ID: nenhum (primeira execução - vai enviar ÚLTIMA)")
        logger.info("")
    logger.info(f"⏱️  Ciclo: Verificar todos → pausar {POLL_SECONDS//60} minutos")
    logger.info("=" * 80)
    logger.info("")
    cycle_count = 0

    async def _check_all_sources():
        for source_group, target_group, description in CHANNEL_PAIRS:
            try:
                logger.info(f"🔹 {description}")
                logger.info(f"   Verificando: {source_group}...")

                await ensure_whatsapp_ready(page_w)
                await open_chat(page_w, source_group)
                await page_w.wait_for_timeout(BUBBLE_REFRESH_DELAY * 1000)

                text, hrefs = await extract_last_message_text_and_urls(page_w)
                if text or hrefs:
                    msg_id = compute_msg_id(text, hrefs)
                    last_seen_id = last_seen_dict.get(source_group)
                    if not last_seen_id:
                        logger.info("   🆕 PRIMEIRA EXECUÇÃO - Enviando ÚLTIMA mensagem")
                        ok = await process_new_message(
                            page_w, page_m, text, hrefs, source_group, target_group, description
                        )
                        if ok:
                            last_seen_dict[source_group] = msg_id
                            preview = text[:50] if text else ""
                            save_last_seen(msg_id, source_group, preview)
                            logger.info(f"   💾 ID salvo: {msg_id[:16]}...")
                        else:
                            logger.warning("   ⚠️  Falhou enviar - ID NÃO salvo")
                    elif msg_id != last_seen_id:
                        logger.info("   🆕 MENSAGEM NOVA DETECTADA!")
                        logger.info(f"   ID atual: {msg_id[:16]}...")
                        logger.info(f"   ID anterior: {last_seen_id[:16]}...")
                        ok = await process_new_message(
                            page_w, page_m, text, hrefs, source_group, target_group, description
                        )
                        if ok:
                            last_seen_dict[source_group] = msg_id
                            preview = text[:50] if text else ""
                            save_last_seen(msg_id, source_group, preview)
                            logger.info(f"   💾 ID salvo: {msg_id[:16]}...")
                        else:
                            logger.warning("   ⚠️  Falhou enviar - ID NÃO salvo")
                    else:
                        logger.info("   ✅ Nenhuma mensagem nova")
                else:
                    logger.info("   ℹ️  Sem mensagens no grupo")
            except Exception as e:
                logger.error(f"❌ Erro ao verificar {source_group}: {e}")
                logger.error(traceback.format_exc())
            await asyncio.sleep(2)

    while True:
        try:
            cycle_count += 1
            await wait_for_day_time()
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"🔄 CICLO #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 80)
            logger.info("")
            await asyncio.wait_for(_check_all_sources(), timeout=CYCLE_TIMEOUT_SECONDS)

            if RESTART_EVERY_CYCLES and cycle_count % RESTART_EVERY_CYCLES == 0:
                logger.warning(
                    f"🔁 Reinício preventivo a cada {RESTART_EVERY_CYCLES} ciclos (agora: {cycle_count})"
                )
                raise RestartRequested("Periodic restart")

            logger.info("")
            logger.info("=" * 80)
            logger.info(f"⏸️  Ciclo completo! Pausando por {POLL_SECONDS//60} minutos...")
            logger.info("=" * 80)
            logger.info("")
            await chunked_sleep(POLL_SECONDS, SLEEP_GRANULARITY_SECONDS, label="Pausa")

        except asyncio.TimeoutError:
            logger.error(f"⏱️  Timeout no ciclo (>{CYCLE_TIMEOUT_SECONDS}s). Reiniciando contexto...")
            raise RestartRequested("Cycle timeout")
        except KeyboardInterrupt:
            logger.info("")
            logger.info("⚠️  Bot interrompido pelo usuário (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(60)


async def run():
    logger.info("🚀 Iniciando bot...")
    cleanup_temp_images(DOWNLOAD_DIR)
    async with async_playwright() as p:
        logger.info(f"🔧 Chrome Profile: {CHROME_USER_DATA_DIR}")
        logger.info(f"🎭 Modo Headless: {HEADLESS}")

        while True:
            ctx = None
            try:
                ctx = await p.chromium.launch_persistent_context(
                    CHROME_USER_DATA_DIR,
                    channel="chrome",
                    headless=HEADLESS,
                    args=[
                        f"--profile-directory={CHROME_PROFILE_DIR_NAME}",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    ],
                    ignore_default_args=["--enable-automation"],
                )

                page_w = ctx.pages[0] if ctx.pages else await ctx.new_page()
                logger.info("📱 Abrindo WhatsApp Web...")
                await page_w.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=240000)
                logger.info("✅ WhatsApp pronto!")

                page_m = await ctx.new_page()
                logger.info("🛒 Abrindo Mercado Livre...")
                try:
                    await page_m.goto(
                        "https://www.mercadolivre.com.br/afiliados",
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )
                    logger.info("✅ Mercado Livre pronto!")
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao abrir ML: {e}")

                logger.info("")
                logger.info("🚀 Iniciando monitoramento...")
                logger.info("")

                await monitoring_loop(page_w, page_m)

                break

            except RestartRequested as e:
                logger.warning(f"♻️  Reiniciando contexto: {e}")
                await asyncio.sleep(5)
            except KeyboardInterrupt:
                logger.info("\n⚠️  Bot interrompido pelo usuário (Ctrl+C)")
                break
            except Exception as e:
                logger.critical(f"❌ ERRO no supervisor: {e}")
                logger.critical(traceback.format_exc())
                await asyncio.sleep(15)
            finally:
                if ctx is not None:
                    try:
                        await ctx.close()
                    except Exception:
                        pass


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Bot interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.critical(f"❌ ERRO FATAL: {e}")
        logger.critical(traceback.format_exc())