"""Site-specific login handler registry."""

from __future__ import annotations

from playwright.async_api import Page

from .saucedemo import SauceDemoHandler

_HANDLERS = [
    SauceDemoHandler(),
]


async def try_auto_login(page: Page) -> str | None:
    """Try each registered handler against the current page.

    Returns a status message if login was performed, or None.
    """
    url = page.url
    for handler in _HANDLERS:
        if handler.matches(url) and await handler.is_login_page(page):
            if await handler.login(page):
                return f"Auto-login completed for {handler.site_name}"
    return None
