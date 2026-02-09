"""
Playwright browser configuration and stealth utilities
"""
import random
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


# Chromium launch arguments for headless operation
CHROMIUM_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-software-rasterizer',
    '--disable-blink-features=AutomationControlled',
    '--disable-features=IsolateOrigins,site-per-process',
    '--window-size=1920,1080',
    '--start-maximized',
    '--disable-infobars',
    '--disable-extensions',
]

# Default user agent
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def create_browser_context(
    playwright,
    tenant_id: str,
    storage_state_path: Optional[str] = None,
    headless: bool = True,
    locale: str = "pt-BR",
    timezone: str = "America/Sao_Paulo"
) -> Tuple[Browser, BrowserContext]:
    """
    Create an isolated browser context for a tenant.
    
    Args:
        playwright: Playwright instance
        tenant_id: Unique tenant identifier
        storage_state_path: Path to storage_state.json for session persistence
        headless: Run in headless mode
        locale: Browser locale
        timezone: Browser timezone
        
    Returns:
        Tuple of (Browser, BrowserContext)
    """
    browser = await playwright.chromium.launch(
        headless=headless,
        args=CHROMIUM_ARGS
    )
    
    context_options = {
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": DEFAULT_USER_AGENT,
        "locale": locale,
        "timezone_id": timezone,
        "bypass_csp": True,
        "java_script_enabled": True,
    }
    
    # Restore session if exists
    if storage_state_path and Path(storage_state_path).exists():
        context_options["storage_state"] = storage_state_path
    
    context = await browser.new_context(**context_options)
    
    # Add anti-detection scripts
    await context.add_init_script("""
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en']
        });
    """)
    
    return browser, context


async def random_delay(min_ms: int = 500, max_ms: int = 2000):
    """
    Add a random human-like delay.
    
    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
    """
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


async def human_type(page: Page, selector: str, text: str, clear_first: bool = True):
    """
    Type text like a human with random delays between keystrokes.
    
    Args:
        page: Playwright page
        selector: Element selector
        text: Text to type
        clear_first: Clear existing text first
    """
    element = page.locator(selector)
    await element.click()
    
    if clear_first:
        await page.keyboard.press("Control+a")
        await asyncio.sleep(random.uniform(0.1, 0.2))
    
    for char in text:
        await element.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.15))


async def random_mouse_movement(page: Page):
    """
    Perform random mouse movement to simulate human behavior.
    
    Args:
        page: Playwright page
    """
    x = random.randint(100, 800)
    y = random.randint(100, 600)
    await page.mouse.move(x, y, steps=random.randint(5, 15))


async def safe_click(page: Page, selector: str, timeout: int = 10000):
    """
    Safely click an element with retry logic.
    
    Args:
        page: Playwright page
        selector: Element selector
        timeout: Maximum time to wait in ms
    """
    try:
        await page.locator(selector).wait_for(state="visible", timeout=timeout)
        await random_delay(200, 500)
        await page.locator(selector).click()
        return True
    except Exception:
        return False


async def wait_for_navigation_complete(page: Page, timeout: int = 30000):
    """
    Wait for page to fully load.
    
    Args:
        page: Playwright page
        timeout: Maximum wait time in ms
    """
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)


async def take_screenshot(page: Page, path: str, full_page: bool = False):
    """
    Take a screenshot for debugging.
    
    Args:
        page: Playwright page
        path: Path to save screenshot
        full_page: Capture full scrollable page
    """
    try:
        await page.screenshot(path=path, full_page=full_page)
    except Exception:
        pass
