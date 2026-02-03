# sender_facebook.py - Postagem na Página do Facebook

import asyncio
from typing import Optional


async def send_facebook_post(
    page,
    page_url: str,
    text: str,
    image_path: Optional[str] = None,
    max_retries: int = 3
) -> bool:
    """Posta na Página do Facebook com texto (link preview automático)"""
    
    for attempt in range(max_retries):
        try:
            print(f"\n🔵 [{attempt+1}/{max_retries}] Postando na Página do Facebook...")
            
            # Abre a página
            await page.goto(page_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            
            # Abre modal de criação
            print(" → Abrindo modal...")
            opened = False
            
            try:
                thinking = page.locator('text="No que você está pensando?"').first
                if await thinking.count() > 0:
                    await thinking.click()
                    await page.wait_for_timeout(2000)
                    opened = True
                    print(" ✓ Modal aberto")
            except Exception:
                pass
            
            if not opened:
                try:
                    await page.evaluate("""
                        () => {
                            const all = document.querySelectorAll('span, div');
                            for (const el of all) {
                                if (el.innerText && el.innerText.includes('pensando') && el.offsetParent !== null) {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    await page.wait_for_timeout(2000)
                    opened = True
                    print(" ✓ Modal aberto (JS)")
                except Exception:
                    pass
            
            if not opened:
                raise RuntimeError("Não conseguiu abrir modal")
            
            # Digita o texto
            await page.wait_for_timeout(1500)
            print(" → Digitando texto...")
            
            textbox = page.locator('div[role="dialog"] div[role="textbox"]').first
            if await textbox.count() == 0:
                textbox = page.locator('div[role="textbox"][contenteditable="true"]').first
            
            if await textbox.count() > 0:
                await textbox.click()
                await page.wait_for_timeout(300)
            
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line:
                    await page.keyboard.type(line, delay=3)
                if i < len(lines) - 1:
                    await page.keyboard.press("Shift+Enter")
            
            print(" ✓ Texto digitado")
            
            # Aguarda preview do link
            await page.wait_for_timeout(4000)
            print(" → Preview carregado")
            
            # Clica em Avançar
            await page.wait_for_timeout(1000)
            print(" → Clicando em Avançar...")
            
            advanced = False
            avancar_selectors = [
                'span:text-is("Avançar")',
                'div[role="button"] span:text-is("Avançar")',
                'div[role="button"]:has-text("Avançar")',
                'text="Avançar"',
            ]
            
            for sel in avancar_selectors:
                if advanced:
                    break
                try:
                    btns = page.locator(sel)
                    count = await btns.count()
                    for i in range(count):
                        btn = btns.nth(i)
                        if await btn.is_visible():
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            advanced = True
                            print(" ✓ Avançou")
                            break
                except Exception:
                    continue
            
            if not advanced:
                try:
                    await page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('span, div[role="button"]');
                            for (const el of elements) {
                                if (el.innerText === 'Avançar') {
                                    el.click();
                                    return true;
                                }
                            }
                        }
                    """)
                    await page.wait_for_timeout(3000)
                    advanced = True
                    print(" ✓ Avançou (JS)")
                except Exception:
                    pass
            
            # Clica em Postar
            await page.wait_for_timeout(2000)
            print(" → Clicando em Postar...")
            
            posted = False
            publicar_selectors = [
                'span:text-is("Postar")',
                'div[role="button"] span:text-is("Postar")',
                'div[role="button"]:has-text("Postar")',
                'text="Postar"',
                'span:text-is("Publicar")',
                'div[role="button"]:has-text("Publicar")',
                'span:text-is("Post")',
                'div[role="button"]:has-text("Post")',
            ]
            
            for sel in publicar_selectors:
                if posted:
                    break
                try:
                    btns = page.locator(sel)
                    count = await btns.count()
                    for i in range(count):
                        btn = btns.nth(i)
                        if await btn.is_visible():
                            await btn.click()
                            await page.wait_for_timeout(4000)
                            posted = True
                            print(" ✅ Publicado!")
                            break
                except Exception:
                    continue
            
            if not posted:
                try:
                    await page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('span, div[role="button"]');
                            for (const el of elements) {
                                if (el.innerText === 'Postar' || el.innerText === 'Publicar' || el.innerText === 'Post') {
                                    el.click();
                                    return true;
                                }
                            }
                        }
                    """)
                    await page.wait_for_timeout(4000)
                    posted = True
                    print(" ✅ Postado (JS)")
                except Exception:
                    pass
            
            if posted:
                print(" ✅✅✅ Post finalizado!")
                return True
            elif advanced:
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(4000)
                print(" ✅ Publicado (via Enter)")
                return True
            else:
                raise RuntimeError("Não conseguiu finalizar o post")
            
        except Exception as e:
            print(f"\n ❌ Tentativa {attempt+1} falhou: {str(e)[:100]}")
            
            try:
                for _ in range(3):
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(300)
                
                await page.wait_for_timeout(500)
                try:
                    descartar = page.locator('text="Descartar"').first
                    if await descartar.count() > 0 and await descartar.is_visible():
                        await descartar.click()
                        await page.wait_for_timeout(1000)
                except Exception:
                    pass
            except Exception:
                pass
            
            if attempt < max_retries - 1:
                print(f" → Retry em 3s...")
                await asyncio.sleep(3)
            else:
                print(" ❌ FALHA FINAL")
                return False
    
    return False
