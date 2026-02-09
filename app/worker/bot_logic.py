"""
Core bot logic - to be customized for your specific use case
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page

from .browser_config import (
    create_browser_context,
    random_delay,
    human_type,
    safe_click,
    wait_for_navigation_complete,
    take_screenshot
)
from .session_manager import TenantSessionManager

logger = logging.getLogger(__name__)


async def execute_bot_logic(
    page: Page,
    config: Dict[str, Any],
    secrets: Dict[str, Any],
    tenant_id: str,
    session_manager: TenantSessionManager
) -> Dict[str, Any]:
    """
    Main bot logic execution.
    Customize this function for your specific use case.
    
    Args:
        page: Playwright page instance
        config: Tenant configuration
        secrets: Decrypted tenant secrets
        tenant_id: Tenant identifier
        session_manager: Session manager for screenshots etc.
        
    Returns:
        Result dictionary with orders_found, actions_taken, errors
    """
    result = {
        "orders_found": 0,
        "actions_taken": 0,
        "errors": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Example: Navigate to a page
        target_url = config.get('target_url', 'https://example.com')
        logger.info(f"[{tenant_id}] Navigating to {target_url}")
        
        await page.goto(target_url)
        await wait_for_navigation_complete(page)
        await random_delay(1000, 2000)
        
        # Take screenshot for debugging
        screenshot_path = session_manager.get_screenshots_dir(tenant_id) / f"step1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await take_screenshot(page, str(screenshot_path))
        
        # Check if login is needed
        if await needs_login(page, config):
            logger.info(f"[{tenant_id}] Login required, performing login...")
            login_success = await perform_login(page, config, secrets)
            if not login_success:
                result["errors"].append("Login failed")
                return result
            result["actions_taken"] += 1
        
        # Execute main task
        # TODO: Customize this for your specific bot logic
        task_result = await execute_main_task(page, config, tenant_id)
        
        result["orders_found"] = task_result.get("items_found", 0)
        result["actions_taken"] += task_result.get("actions", 0)
        result["data"] = task_result.get("data", {})
        
    except Exception as e:
        logger.exception(f"[{tenant_id}] Error in bot logic: {e}")
        result["errors"].append(str(e))
        
        # Take error screenshot
        try:
            error_screenshot = session_manager.get_screenshots_dir(tenant_id) / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await take_screenshot(page, str(error_screenshot), full_page=True)
        except Exception:
            pass
    
    return result


async def needs_login(page: Page, config: Dict[str, Any]) -> bool:
    """
    Check if login is required.
    Customize based on your target platform.
    
    Args:
        page: Playwright page
        config: Tenant configuration
        
    Returns:
        True if login is needed
    """
    # Example: Check for login button or redirect to login page
    try:
        # Look for common login indicators
        login_indicators = [
            'input[type="password"]',
            'button:has-text("Sign in")',
            'a:has-text("Login")',
            '#login-form',
        ]
        
        for selector in login_indicators:
            if await page.locator(selector).count() > 0:
                return True
        
        # Check URL for login page patterns
        current_url = page.url.lower()
        if any(x in current_url for x in ['login', 'signin', 'auth']):
            return True
        
        return False
        
    except Exception:
        return False


async def perform_login(
    page: Page,
    config: Dict[str, Any],
    secrets: Dict[str, Any]
) -> bool:
    """
    Perform login to target platform.
    Customize for your specific platform.
    
    Args:
        page: Playwright page
        config: Tenant configuration
        secrets: Decrypted secrets (passwords etc.)
        
    Returns:
        True if login successful
    """
    try:
        email = config.get('platform_email') or secrets.get('platform_email')
        password = secrets.get('platform_password') or config.get('platform_password')
        
        if not email or not password:
            logger.error("Login credentials not configured")
            return False
        
        # Example login flow - customize for your platform
        await random_delay(500, 1000)
        
        # Type email
        email_selector = config.get('login_email_selector', 'input[type="email"], input[name="email"], #email')
        await human_type(page, email_selector, email)
        await random_delay(300, 600)
        
        # Type password
        password_selector = config.get('login_password_selector', 'input[type="password"]')
        await human_type(page, password_selector, password)
        await random_delay(300, 600)
        
        # Click submit
        submit_selector = config.get('login_submit_selector', 'button[type="submit"], input[type="submit"]')
        await safe_click(page, submit_selector)
        
        # Wait for navigation
        await wait_for_navigation_complete(page, timeout=30000)
        await random_delay(2000, 4000)
        
        # Verify login success
        if not await needs_login(page, config):
            logger.info("Login successful")
            return True
        
        logger.warning("Login may have failed - still seeing login elements")
        return False
        
    except Exception as e:
        logger.exception(f"Login error: {e}")
        return False


async def execute_main_task(
    page: Page,
    config: Dict[str, Any],
    tenant_id: str
) -> Dict[str, Any]:
    """
    Execute the main bot task.
    This is where you implement your specific automation logic.
    
    Args:
        page: Playwright page
        config: Tenant configuration
        tenant_id: Tenant identifier
        
    Returns:
        Task results dictionary
    """
    result = {
        "items_found": 0,
        "actions": 0,
        "data": {}
    }
    
    try:
        # TODO: Implement your specific bot logic here
        # Examples:
        # - Scrape data
        # - Check for new orders
        # - Process items
        # - Send notifications
        
        logger.info(f"[{tenant_id}] Executing main task...")
        
        # Placeholder: Get page title as example
        title = await page.title()
        result["data"]["page_title"] = title
        result["items_found"] = 1
        result["actions"] = 1
        
        logger.info(f"[{tenant_id}] Main task completed")
        
    except Exception as e:
        logger.exception(f"[{tenant_id}] Main task error: {e}")
        raise
    
    return result


async def execute_test_run(
    tenant_id: str,
    dry_run: bool = True,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Execute a single test run of the bot.
    Uses incognito mode (no session persistence).
    
    Args:
        tenant_id: Tenant identifier
        dry_run: If True, don't execute destructive actions
        timeout: Maximum execution time in seconds
        
    Returns:
        Test run results
    """
    from ..db.database import get_pool
    from .config_loader import TenantConfigLoader
    
    result = {
        "orders_found": 0,
        "actions_taken": 0,
        "errors": []
    }
    
    async def run_with_timeout():
        pool = await get_pool()
        config_loader = TenantConfigLoader(pool)
        session_manager = TenantSessionManager()
        
        config = await config_loader.get_tenant_config(tenant_id)
        secrets = await config_loader.get_tenant_secrets(tenant_id)
        
        async with async_playwright() as p:
            # Don't use stored session for test runs
            browser, context = await create_browser_context(
                p,
                tenant_id,
                storage_state_path=None,  # No session persistence
                headless=config.get('headless', True)
            )
            
            try:
                page = await context.new_page()
                
                bot_result = await execute_bot_logic(
                    page=page,
                    config=config,
                    secrets=secrets,
                    tenant_id=tenant_id,
                    session_manager=session_manager
                )
                
                result["orders_found"] = bot_result.get("orders_found", 0)
                result["actions_taken"] = bot_result.get("actions_taken", 0)
                result["errors"] = bot_result.get("errors", [])
                
            finally:
                await context.close()
                await browser.close()
    
    try:
        await asyncio.wait_for(run_with_timeout(), timeout=timeout)
    except asyncio.TimeoutError:
        result["errors"].append(f"Test run timed out after {timeout} seconds")
    except Exception as e:
        result["errors"].append(str(e))
    
    return result
