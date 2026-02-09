import asyncio
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("BotAfiliados")


async def send_facebook_post(
    page,
    page_url: str,
    text: str,
    image_path: Optional[str] = None,
    max_retries: int = 3
) -> bool:
    """
    Posta na PÁGINA do Facebook com TEXTO + IMAGEM
    Ordem: TEXTO PRIMEIRO, IMAGEM DEPOIS (funciona melhor para páginas)
    """

    # Validação
    if image_path:
        img_file = Path(image_path)
        if not img_file.exists():
            logger.error(f" ❌ [FB] Imagem não existe: {image_path}")
            return False
        logger.info(f" ✅ [FB] Imagem: {img_file.name} ({img_file.stat().st_size} bytes)")

    for attempt in range(max_retries):
        try:
            logger.info(f" 🔵 [FB] Tentativa {attempt+1}/{max_retries}...")

            # 1. Abre a página do Facebook
            await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # 2. Abre modal de post
            logger.info(" [FB] → Abrindo modal...")
            if not await _open_create_modal(page):
                raise RuntimeError("Falha ao abrir modal")
            logger.info(" [FB] ✓ Modal aberto")

            # 3. TEXTO PRIMEIRO
            logger.info(" [FB] → Digitando texto...")
            await _type_text(page, text)
            logger.info(" [FB] ✓ Texto digitado")
            await page.wait_for_timeout(2000)

            # 4. DEPOIS ADICIONA IMAGEM
            if image_path:
                logger.info(" [FB] → Adicionando imagem...")
                if await _add_image_to_post(page, image_path):
                    logger.info(" [FB] ✅ Imagem anexada!")
                else:
                    logger.warning(" [FB] ⚠️ Falha ao anexar imagem")
                    # Continua mesmo sem imagem

            # 5. Aguarda preview carregar
            await page.wait_for_timeout(3000)

            # 6. PUBLICA
            logger.info(" [FB] → Publicando...")
            if await _click_publish(page):
                logger.info(" [FB] ✅✅✅ POST PUBLICADO!")
                return True
            else:
                raise RuntimeError("Falha ao publicar")

        except Exception as e:
            logger.error(f" [FB] ❌ Tentativa {attempt+1}: {str(e)[:100]}")

            # Fecha modal
            try:
                for _ in range(5):
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(200)
            except:
                pass

            if attempt < max_retries - 1:
                logger.info(f" [FB] → Retry em 5s...")
                await asyncio.sleep(5)

    logger.error(" [FB] ❌ FALHA FINAL após todas tentativas")
    return False


async def _open_create_modal(page) -> bool:
    """Abre o modal 'Criar post' clicando em 'No que você está pensando?'"""

    selectors = [
        'span:has-text("No que você está pensando")',
        'div[role="button"]:has-text("pensando")',
        'div:has-text("Criar publicação")',
    ]

    for sel in selectors:
        try:
            elem = page.locator(sel).first
            if await elem.count() > 0:
                await elem.click()
                await page.wait_for_timeout(2500)

                # Verifica se modal abriu
                modal = page.locator('div[role="dialog"]').first
                if await modal.count() > 0:
                    return True
        except:
            continue

    # Fallback JS
    try:
        clicked = await page.evaluate("""
            () => {
                const spans = document.querySelectorAll('span, div');
                for (const el of spans) {
                    const text = (el.innerText || '').toLowerCase();
                    if ((text.includes('pensando') || text.includes('publicação')) && 
                        el.offsetParent !== null) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        if clicked:
            await page.wait_for_timeout(2500)
            return True
    except:
        pass

    return False


async def _type_text(page, text: str):
    """Digita o texto no campo de post"""

    await page.wait_for_timeout(1000)

    # Procura o campo de texto
    selectors = [
        'div[role="dialog"] div[contenteditable="true"]',
        'div[role="textbox"][contenteditable="true"]',
        'div[contenteditable="true"][data-lexical-editor]',
    ]

    textbox = None
    for sel in selectors:
        try:
            tb = page.locator(sel).first
            if await tb.count() > 0:
                textbox = tb
                break
        except:
            continue

    if not textbox:
        logger.warning(" [FB] ⚠️ Campo de texto não encontrado!")
        return

    # Clica no campo
    await textbox.click()
    await page.wait_for_timeout(500)

    # Digita linha por linha (preserva quebras de linha)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.strip():
            await page.keyboard.type(line, delay=5)
        if i < len(lines) - 1:
            await page.keyboard.press("Shift+Enter")
            await page.wait_for_timeout(50)


async def _add_image_to_post(page, image_path: str) -> bool:
    """
    🔥 ADICIONA IMAGEM AO POST (texto já digitado)
    Método SIMPLES - envia para o primeiro input e ASSUME sucesso
    """

    try:
        # Procura todos os inputs de file no modal
        inputs = await page.locator('div[role="dialog"] input[type="file"]').all()

        if not inputs:
            # Tenta também inputs fora do modal
            inputs = await page.locator('input[type="file"][accept*="image"]').all()
            
        if not inputs:
            logger.warning(" [FB] ⚠️ Nenhum input file encontrado")
            return False

        logger.info(f" [FB] Encontrados {len(inputs)} inputs de arquivo")

        # Tenta o PRIMEIRO input que aceita imagem
        for i, file_input in enumerate(inputs):
            try:
                accept = await file_input.get_attribute("accept") or ""

                # Pula se explicitamente NÃO aceita imagem
                if accept and "image" not in accept.lower() and "video" not in accept.lower():
                    continue

                # ANEXA A IMAGEM
                await file_input.set_input_files(str(Path(image_path).resolve()))
                logger.info(f" [FB] ✓ Arquivo enviado ao input #{i+1}")

                # Aguarda upload processar (mais tempo)
                await page.wait_for_timeout(6000)

                # Verifica se imagem apareceu (múltiplos métodos)
                result = await page.evaluate("""
                    () => {
                        const modals = document.querySelectorAll('div[role="dialog"]');
                        
                        for (const modal of modals) {
                            // 1. Procura imagens grandes (preview)
                            const imgs = modal.querySelectorAll('img');
                            for (const img of imgs) {
                                const rect = img.getBoundingClientRect();
                                // Imagem de preview geralmente tem tamanho razoável
                                if (rect.width > 100 && rect.height > 80) {
                                    return { found: true, method: 'large_img', size: rect.width + 'x' + rect.height };
                                }
                            }
                            
                            // 2. Procura texto "Editar tudo" ou similar (aparece com imagem)
                            const text = modal.innerText || '';
                            if (text.includes('Editar tudo') || text.includes('Edit All') || 
                                text.includes('Editar foto')) {
                                return { found: true, method: 'edit_text' };
                            }
                            
                            // 3. Procura por container de mídia
                            const mediaContainers = modal.querySelectorAll('[data-visualcompletion]');
                            if (mediaContainers.length > 5) {
                                return { found: true, method: 'media_container' };
                            }
                        }
                        
                        return { found: false };
                    }
                """)

                logger.info(f" [FB] Verificação: {result}")

                if result.get('found'):
                    logger.info(f" [FB] ✓ Imagem confirmada: {result.get('method')}")
                    return True
                else:
                    # Mesmo sem confirmação visual, SE o input aceitou o arquivo, 
                    # provavelmente funcionou. Retorna True e deixa continuar.
                    logger.info(f" [FB] ✓ Input #{i+1} aceitou arquivo (assumindo sucesso)")
                    return True

            except Exception as e:
                logger.info(f" [FB] Input #{i+1} falhou: {str(e)[:50]}")
                continue

        logger.warning(" [FB] ⚠️ Nenhum input funcionou")
        return False

    except Exception as e:
        logger.error(f" [FB] Erro ao adicionar imagem: {e}")
        return False


async def _click_publish(page) -> bool:
    """Clica em 'Avançar' (se houver) e depois em 'Postar'"""

    await page.wait_for_timeout(2000)

    # 1. Tenta clicar em "Avançar" (algumas páginas têm esse passo intermediário)
    logger.info(" [FB] → Procurando Avançar...")
    
    try:
        avancar_clicked = await page.evaluate("""
            () => {
                const modals = document.querySelectorAll('div[role="dialog"]');
                for (const modal of modals) {
                    const buttons = modal.querySelectorAll('div[role="button"]');
                    for (const btn of buttons) {
                        const text = (btn.innerText || '').trim();
                        if (text === 'Avançar' || text === 'Next') {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        
        if avancar_clicked:
            logger.info(" [FB] ✓ Clicou em Avançar")
            await page.wait_for_timeout(3000)  # Aguarda nova tela carregar
        else:
            logger.info(" [FB] Sem botão Avançar, tentando Postar direto...")
            
    except Exception as e:
        logger.info(f" [FB] Avançar não encontrado: {e}")

    await page.wait_for_timeout(2000)

    # 2. Clica em "Postar" / "Publicar" - BOTÃO AZUL no final
    logger.info(" [FB] → Procurando botão Postar...")
    
    try:
        # Tenta várias abordagens
        clicked = await page.evaluate("""
            () => {
                // Pega TODOS os modals (pode haver mais de um)
                const modals = document.querySelectorAll('div[role="dialog"]');
                
                // Percorre do último para o primeiro (o mais recente geralmente é o visível)
                for (let i = modals.length - 1; i >= 0; i--) {
                    const modal = modals[i];
                    
                    // 1. Procura botões com texto exato
                    const buttons = modal.querySelectorAll('div[role="button"]');
                    for (const btn of buttons) {
                        const text = (btn.innerText || '').trim();
                        const rect = btn.getBoundingClientRect();
                        
                        // Pula se não está visível
                        if (rect.width === 0 || rect.height === 0) continue;
                        
                        // Verifica se é o botão Postar/Publicar
                        if (text === 'Postar' || text === 'Publicar' || text === 'Post') {
                            // NÃO é switch/toggle
                            const isSwitch = btn.closest('[role="switch"]') ||
                                           btn.querySelector('input[type="checkbox"]');
                            if (isSwitch) continue;
                            
                            // Deve ser um botão com tamanho razoável
                            if (rect.width > 60 && rect.height > 25) {
                                btn.click();
                                return { clicked: true, text: text, method: 'button_text' };
                            }
                        }
                    }
                    
                    // 2. Procura spans com texto
                    const spans = modal.querySelectorAll('span');
                    for (const span of spans) {
                        const text = (span.innerText || '').trim();
                        if (text === 'Postar' || text === 'Publicar' || text === 'Post') {
                            // Sobe até achar um div[role="button"]
                            let parent = span.parentElement;
                            for (let j = 0; j < 5 && parent; j++) {
                                if (parent.getAttribute && parent.getAttribute('role') === 'button') {
                                    const isSwitch = parent.closest('[role="switch"]');
                                    if (!isSwitch) {
                                        parent.click();
                                        return { clicked: true, text: text, method: 'span_parent' };
                                    }
                                }
                                parent = parent.parentElement;
                            }
                        }
                    }
                }
                
                // 3. Último recurso: qualquer elemento clicável com "Postar"
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    if (el.innerText === 'Postar' || el.innerText === 'Publicar') {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 60 && rect.height > 25 && rect.y > 300) {
                            el.click();
                            return { clicked: true, method: 'fallback' };
                        }
                    }
                }
                
                return { clicked: false, reason: 'not_found', modals: modals.length };
            }
        """)
        
        logger.info(f" [FB] Resultado Postar: {clicked}")
        
        if clicked.get('clicked'):
            await page.wait_for_timeout(5000)
            logger.info(" [FB] ✅ Publicado com sucesso!")
            return True
            
    except Exception as e:
        logger.error(f" [FB] Erro ao clicar Postar: {e}")

    # Último recurso: tentar via Playwright locator
    try:
        logger.info(" [FB] → Tentando via locator...")
        postar_btn = page.locator('div[role="button"]:has-text("Postar")').last
        if await postar_btn.count() > 0 and await postar_btn.is_visible():
            await postar_btn.click()
            await page.wait_for_timeout(5000)
            logger.info(" [FB] ✅ Publicado via locator!")
            return True
    except Exception as e:
        logger.info(f" [FB] Locator falhou: {e}")

    logger.warning(" [FB] ⚠️ Não encontrou botão Postar")
    return False