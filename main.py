# main.py - Bot de Afiliados WhatsApp + Facebook

import asyncio
import traceback
import random
import os
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

from config import (
    BUBBLE_REFRESH_DELAY,
    CHANNEL_PAIRS,
    DOWNLOAD_DIR,
    MELI_AFFILIATE_TAG,
    CHROME_USER_DATA_DIR,
    AMAZON_AFFILIATE_TAG,
    AMAZON_ENABLED,
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
    GROUP_LINK,
    LOG_CLEANUP_CYCLES,
    FACEBOOK_ENABLED,
    FACEBOOK_PAGE_URL,
    FACEBOOK_POST_INTERVAL,
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
    filter_amazon_urls,
    format_old_price_with_strikethrough,
    remove_text_formatting,
)

from affiliate import generate_affiliate_link, generate_amazon_affiliate_link_async
from sender_whatsapp import send_image_with_caption
from sender_facebook import send_facebook_post
from storage import get_last_seen as load_last_seen, save_last_seen
from dedup import is_duplicate, mark_as_sent, cleanup_expired_cache

# Variáveis globais
CURRENT_LOG_FILE = None
last_facebook_post_time = None
facebook_source_index = 0  # Índice do grupo atual para rotação no Facebook


def setup_logger():
    """Configura o sistema de logs com arquivo e console."""
    global CURRENT_LOG_FILE
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    CURRENT_LOG_FILE = log_file
    
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


def rotate_logs():
    """Fecha o log atual, deleta e inicia um novo."""
    global CURRENT_LOG_FILE, logger
    
    logger = logging.getLogger("BotAfiliados")
    if logger.hasHandlers():
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
    
    if CURRENT_LOG_FILE and CURRENT_LOG_FILE.exists():
        try:
            os.remove(CURRENT_LOG_FILE)
            print(f"🗑️ [SISTEMA] Log antigo deletado: {CURRENT_LOG_FILE.name}")
        except Exception as e:
            print(f"⚠️ [SISTEMA] Falha ao deletar log: {e}")
    
    setup_logger()
    logger.info("♻️ Logs reiniciados")


class RestartRequested(Exception):
    """Força reinício do navegador."""


async def chunked_sleep(total_seconds: int, chunk_seconds: int, *, label: str = ""):
    """Pausa em chunks para não travar o bot."""
    remaining = max(0, int(total_seconds))
    chunk = max(1, int(chunk_seconds))
    while remaining > 0:
        step = min(chunk, remaining)
        await asyncio.sleep(step)
        remaining -= step
        if remaining > 0 and label:
            logger.info(f" ⏳ {label}: {remaining}s restantes...")


async def ensure_whatsapp_ready(page_w):
    """Verifica se o WhatsApp está funcionando, tenta recarregar se necessário."""
    try:
        await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=15000)
        return
    except Exception:
        logger.warning("⚠️ WhatsApp travado, recarregando...")
        try:
            await page_w.reload(wait_until="domcontentloaded", timeout=60000)
            await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=60000)
            logger.info("✅ WhatsApp voltou!")
        except Exception as e:
            logger.error(f"❌ WhatsApp não voltou: {e}")
            raise RestartRequested("WhatsApp não está pronto")


def process_text_enhancements(text: str) -> str:
    """Remove emoji específico e adiciona gatilhos aleatórios."""
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
        logger.info(f" 🧹 Removido emoji: {SUPERHERO_EMOJI}")
    
    if random.random() < GATILHO_CHANCE:
        gatilho = random.choice(GATILHOS)
        text = f"{gatilho}\n\n{text}"
        logger.info(f" ✨ Gatilho adicionado: {gatilho}")
    
    return text


def filter_meli_sec_urls(urls: list[str]) -> list[str]:
    """Filtra URLs do Mercado Livre com /sec/."""
    if not urls:
        return []
    meli_sec_pattern = re.compile(r"mercadolivre\..*?/sec/", re.IGNORECASE)
    return [u for u in urls if u and meli_sec_pattern.search(u)]


def cleanup_temp_images(download_dir: str):
    """Limpa imagens temporárias da pasta tmp."""
    try:
        temp_dir = Path(download_dir)
        if not temp_dir.exists():
            return
        for img_file in temp_dir.glob("*.jpg"):
            try:
                img_file.unlink()
            except Exception:
                pass
        logger.info("🗑️ Cleanup: imagens temporárias deletadas")
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar imagens: {e}")


async def wait_for_day_time():
    """Pausa o bot durante o horário noturno."""
    if not NIGHT_MODE_ENABLED:
        return
    
    now = datetime.now()
    current_hour = now.hour
    
    if NIGHT_START_HOUR <= current_hour < NIGHT_END_HOUR or (
        NIGHT_START_HOUR > NIGHT_END_HOUR
        and (current_hour >= NIGHT_START_HOUR or current_hour < NIGHT_END_HOUR)
    ):
        logger.info(f"🌙 Modo noturno ativo ({NIGHT_START_HOUR:02d}:00-{NIGHT_END_HOUR:02d}:00)")
        logger.info(f"⏸️ Pausando até {NIGHT_END_HOUR:02d}:00...")
        
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
                logger.info("☀️ Modo diurno - retomando!")
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
    """Processa e envia mensagem nova do WhatsApp."""
    bubble = await get_last_message_bubble(page_w)
    if not await has_image(bubble):
        logger.warning(f" ⚠️ {source_name}: Sem imagem - ignorando")
        return True
    
    logger.info(f" 📸 {source_name}: Tem imagem ✅")
    
    urls = hrefs if hrefs else extract_urls_from_text(text)
    
    if is_duplicate(target_name, text, urls):
        logger.warning(f" 🔄 {source_name}: Duplicada - ignorando (bloqueio 3h)")
        return True
    
    meli_urls = filter_meli_sec_urls(urls)
    amazon_urls = filter_amazon_urls(urls) if AMAZON_ENABLED else []
    
    mapping = {}
    product_url = None
    platform = None
    
    if meli_urls:
        platform = "ML"
        for u in meli_urls[:3]:
            logger.info(f" 🔗 [ML] Gerando afiliado: {u[:60]}...")
            new_u, prod_url = await generate_affiliate_link(page_m, u, MELI_AFFILIATE_TAG)
            if new_u:
                mapping[u] = new_u
                product_url = prod_url
                logger.info(f" ✅ [ML] Gerado!")
                break
    elif amazon_urls:
        platform = "AMAZON"
        for u in amazon_urls[:3]:
            logger.info(f" 🔗 [AMAZON] Gerando afiliado: {u[:60]}...")
            new_u, prod_url = await generate_amazon_affiliate_link_async(
                page_m, u, AMAZON_AFFILIATE_TAG
            )
            if new_u:
                mapping[u] = new_u
                product_url = prod_url
                logger.info(f" ✅ [AMAZON] Gerado!")
                break
    else:
        logger.warning(f" ⚠️ {source_name}: Sem link ML ou Amazon - ignorando")
        return True
    
    if not mapping:
        logger.error(f" ❌ {source_name}: Falha ao gerar afiliado [{platform}]")
        return False
    
    enhanced_text = process_text_enhancements(text)
    new_text = replace_urls_in_text(enhanced_text, mapping)
    new_text = format_old_price_with_strikethrough(new_text)
    final_text = new_text
    
    logger.info(f" 📝 Texto: {len(final_text)} chars")
    preview = final_text.replace("\n", " ")[:80]
    logger.info(f" 📝 Preview: {preview}...")
    
    logger.info(f" 📸 Baixando imagem...")
    img_path = await download_last_image(page_w, DOWNLOAD_DIR, source_name)
    if not img_path:
        logger.error(f" ❌ {source_name}: Falha ao baixar imagem")
        return False
    
    logger.info(f" ✅ Imagem pronta: {os.path.basename(img_path)}")
    
    await page_w.bring_to_front()
    await page_w.wait_for_timeout(300)
    
    logger.info(f" 📤 Enviando para {target_name}...")
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
            logger.info(f" 🗑️ Imagem temporária deletada")
        except Exception as e:
            logger.warning(f" ⚠️ Erro ao deletar imagem: {e}")
    
    if ok:
        logger.info(f" ✅✅✅ {source_name}: SUCESSO!")
        mark_as_sent(target_name, text, urls)
    else:
        logger.error(f" ❌ {source_name}: FALHA")
    
    return ok


async def maybe_post_to_facebook(page_w, page_m, page_fb, last_post_time):
    """
    Posta no Facebook a cada X minutos, rotacionando entre os grupos fonte.
    Cada postagem usa um grupo diferente (Herói, Home Deals, Tech Deals, etc).
    """
    global facebook_source_index
    
    if not FACEBOOK_ENABLED or not page_fb:
        return last_post_time
    
    now = datetime.now()
    
    if last_post_time is None or (now - last_post_time).total_seconds() >= FACEBOOK_POST_INTERVAL:
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📘 FACEBOOK: Hora de postar!")
        if last_post_time:
            elapsed = int((now - last_post_time).total_seconds() / 60)
            logger.info(f" ⏱️ Última postagem: {elapsed} min atrás")
        else:
            logger.info(f" ⏱️ Primeira postagem do dia")
        logger.info("=" * 80)
        
        # Rotaciona entre os grupos - cada post usa um grupo diferente
        source_group, target_group, description = CHANNEL_PAIRS[facebook_source_index]
        logger.info(f" 📋 Grupo da vez: {description} (índice {facebook_source_index})")
        
        # Atualiza índice para o próximo grupo
        facebook_source_index = (facebook_source_index + 1) % len(CHANNEL_PAIRS)
        
        try:
            await ensure_whatsapp_ready(page_w)
            await open_chat(page_w, source_group)
            await page_w.wait_for_timeout(BUBBLE_REFRESH_DELAY * 1000)
            
            text, hrefs = await extract_last_message_text_and_urls(page_w)
            
            if not text and not hrefs:
                logger.warning(" ⚠️ Facebook: Nenhuma mensagem no grupo")
                logger.info("=" * 80)
                return last_post_time
            
            bubble = await get_last_message_bubble(page_w)
            if not await has_image(bubble):
                logger.warning(" ⚠️ Facebook: Sem imagem - ignorando")
                logger.info("=" * 80)
                return last_post_time
            
            logger.info(f" 📸 Mensagem tem imagem ✅")
            
            urls = hrefs if hrefs else extract_urls_from_text(text)
            meli_urls = filter_meli_sec_urls(urls)
            amazon_urls = filter_amazon_urls(urls) if AMAZON_ENABLED else []
            
            mapping = {}
            platform = None
            
            if meli_urls:
                platform = "ML"
                for u in meli_urls[:3]:
                    logger.info(f" 🔗 [FB→ML] Gerando afiliado...")
                    new_u, prod_url = await generate_affiliate_link(page_m, u, MELI_AFFILIATE_TAG)
                    if new_u:
                        mapping[u] = new_u
                        logger.info(f" ✅ [FB→ML] Gerado!")
                        break
            elif amazon_urls:
                platform = "AMAZON"
                for u in amazon_urls[:3]:
                    logger.info(f" 🔗 [FB→AMAZON] Gerando afiliado...")
                    new_u, prod_url = await generate_amazon_affiliate_link_async(
                        page_m, u, AMAZON_AFFILIATE_TAG
                    )
                    if new_u:
                        mapping[u] = new_u
                        logger.info(f" ✅ [FB→AMAZON] Gerado!")
                        break
            
            if not mapping:
                logger.warning(f" ⚠️ Facebook: Sem link afiliado - ignorando")
                logger.info("=" * 80)
                return last_post_time
            
            enhanced_text = process_text_enhancements(text)
            final_text = replace_urls_in_text(enhanced_text, mapping)
            final_text = format_old_price_with_strikethrough(final_text)
            final_text = remove_text_formatting(final_text)
            
            if GROUP_LINK:
                final_text = final_text.replace(f"\n\n☑️ Link do grupo: {GROUP_LINK}", "")
                final_text += f"\n\n📲 Entre no nosso grupo do WhatsApp:\n{GROUP_LINK}"
            
            logger.info(f" 📝 Texto: {len(final_text)} chars")
            preview = final_text.replace("\n", " ")[:80]
            logger.info(f" 📝 Preview: {preview}...")
            
            await page_fb.bring_to_front()
            await page_fb.wait_for_timeout(500)
            
            logger.info(f" 📤 Postando no Facebook...")
            ok = await send_facebook_post(page_fb, FACEBOOK_PAGE_URL, final_text)
            
            if ok:
                logger.info(" ✅✅✅ Facebook: SUCESSO!")
                logger.info("=" * 80)
                return now
            else:
                logger.error(" ❌ Facebook: FALHA")
                logger.info("=" * 80)
                return last_post_time
                
        except Exception as e:
            logger.error(f"❌ Erro no Facebook: {e}")
            logger.error(traceback.format_exc())
            logger.info("=" * 80)
            return last_post_time
    
    return last_post_time


async def monitoring_loop(page_w, page_m, page_fb):
    """Loop principal de monitoramento."""
    global last_facebook_post_time
    
    last_seen_dict = {}
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🤖 BOT INICIADO - WhatsApp + Facebook")
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
            logger.info(f"   Último ID: nenhum")
        logger.info("")
    
    if FACEBOOK_ENABLED:
        logger.info(f"📘 Facebook: ATIVADO")
        logger.info(f"   Página: {FACEBOOK_PAGE_URL}")
        logger.info(f"   Intervalo: {FACEBOOK_POST_INTERVAL // 60} min")
        logger.info(f"   Rotação: {len(CHANNEL_PAIRS)} grupos")
        logger.info("")
    else:
        logger.info(f"📘 Facebook: DESATIVADO")
        logger.info("")
    
    logger.info(f"⏱️  Ciclo: {POLL_SECONDS//60} minutos")
    logger.info("=" * 80)
    
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
                        logger.info("   🆕 Primeira execução - enviando última mensagem")
                        ok = await process_new_message(
                            page_w, page_m, text, hrefs, source_group, target_group, description
                        )
                        if ok:
                            last_seen_dict[source_group] = msg_id
                            preview = text[:50] if text else ""
                            save_last_seen(msg_id, source_group, preview)
                            logger.info(f"   💾 ID salvo")
                        else:
                            logger.warning("   ⚠️ Falhou - ID não salvo")
                    
                    elif msg_id != last_seen_id:
                        logger.info("   🆕 MENSAGEM NOVA!")
                        ok = await process_new_message(
                            page_w, page_m, text, hrefs, source_group, target_group, description
                        )
                        if ok:
                            last_seen_dict[source_group] = msg_id
                            preview = text[:50] if text else ""
                            save_last_seen(msg_id, source_group, preview)
                            logger.info(f"   💾 ID salvo")
                        else:
                            logger.warning("   ⚠️ Falhou - ID não salvo")
                    else:
                        logger.info("   ✅ Sem novidades")
                else:
                    logger.info("   ℹ️ Sem mensagens")
            
            except Exception as e:
                logger.error(f"❌ Erro em {source_group}: {e}")
                logger.error(traceback.format_exc())
            
            await asyncio.sleep(2)
    
    while True:
        try:
            cycle_count += 1
            
            if LOG_CLEANUP_CYCLES > 0 and cycle_count % LOG_CLEANUP_CYCLES == 0:
                logger.info(f"🧹 Limpando logs (Ciclo {cycle_count})...")
                rotate_logs()
            
            if cycle_count % 10 == 0:
                cleanup_expired_cache()
            
            await wait_for_day_time()
            
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"🔄 CICLO #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info("=" * 80)
            
            await asyncio.wait_for(_check_all_sources(), timeout=CYCLE_TIMEOUT_SECONDS)
            
            last_facebook_post_time = await maybe_post_to_facebook(
                page_w, page_m, page_fb, last_facebook_post_time
            )
            
            if RESTART_EVERY_CYCLES and cycle_count % RESTART_EVERY_CYCLES == 0:
                logger.warning(f"🔁 Reinício preventivo (ciclo {cycle_count})")
                raise RestartRequested("Reinício periódico")
            
            logger.info("")
            logger.info(f"⏸️ Pausando {POLL_SECONDS//60} min...")
            logger.info("=" * 80)
            
            await chunked_sleep(POLL_SECONDS, SLEEP_GRANULARITY_SECONDS, label="Pausa")
        
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Timeout no ciclo. Reiniciando...")
            raise RestartRequested("Timeout")
        
        except KeyboardInterrupt:
            logger.info("\n⚠️ Bot interrompido (Ctrl+C)")
            break
        
        except Exception as e:
            logger.error(f"❌ Erro no loop: {e}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(60)


async def run():
    """Função principal - inicializa o navegador e páginas."""
    global last_facebook_post_time
    
    logger.info("🚀 Iniciando bot...")
    cleanup_temp_images(DOWNLOAD_DIR)
    
    async with async_playwright() as p:
        logger.info(f"🔧 Chrome Profile: {CHROME_USER_DATA_DIR}")
        logger.info(f"🎭 Headless: {HEADLESS}")
        
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
                
                # WhatsApp
                page_w = ctx.pages[0] if ctx.pages else await ctx.new_page()
                logger.info("📱 Abrindo WhatsApp Web...")
                await page_w.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
                await page_w.wait_for_selector('div[contenteditable="true"][data-tab]', timeout=240000)
                logger.info("✅ WhatsApp pronto!")
                
                # Mercado Livre
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
                    logger.warning(f"⚠️ Erro ML: {e}")
                
                # Amazon
                if AMAZON_ENABLED:
                    logger.info("🛒 Abrindo Amazon...")
                    try:
                        await page_m.goto("https://www.amazon.com.br", wait_until="domcontentloaded")
                        logger.info("✅ Amazon pronta!")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro Amazon: {e}")
                
                # Facebook
                if FACEBOOK_ENABLED:
                    page_fb = await ctx.new_page()
                    logger.info("📘 Abrindo Facebook...")
                    try:
                        await page_fb.goto("https://www.facebook.com", wait_until="domcontentloaded", timeout=60000)
                        await page_fb.wait_for_timeout(3000)
                        logger.info("✅ Facebook pronto!")
                    except Exception as e:
                        logger.warning(f"⚠️ Erro Facebook: {e}")
                        page_fb = None
                else:
                    page_fb = None
                    logger.info("ℹ️ Facebook desativado")
                
                logger.info("")
                logger.info("🚀 Monitoramento iniciado!")
                
                last_facebook_post_time = None
                
                await monitoring_loop(page_w, page_m, page_fb)
                break
            
            except RestartRequested as e:
                logger.warning(f"♻️ Reiniciando: {e}")
                await asyncio.sleep(5)
            
            except KeyboardInterrupt:
                logger.info("\n⚠️ Bot interrompido (Ctrl+C)")
                break
            
            except Exception as e:
                logger.critical(f"❌ ERRO: {e}")
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
        logger.info("\n⚠️ Bot encerrado")
    except Exception as e:
        logger.critical(f"❌ ERRO FATAL: {e}")
        logger.critical(traceback.format_exc())
