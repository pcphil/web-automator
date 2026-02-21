"""Deterministic login handler for saucedemo.com."""

from __future__ import annotations

import os

from playwright.async_api import Page

from .base import SiteHandler


class udemy(SiteHandler):

    @property
    def site_name(self) -> str:
        return "Udemy"

    def matches(self, url: str) -> bool:
        return "udemy.com" in url

    async def is_login_page(self, page: Page) -> bool:
        return await page.locator("#login-button").count() > 0

    async def login(self, page: Page) -> bool:
        username = os.getenv("UDMEY_USERNAME")
        password = os.getenv("UDMEY_PASSWORD")
        if not username or not password:
            return False

        await page.locator("#user-name").fill(username)
        await page.locator("#password").fill(password)
        await page.locator("#login-button").click()
        await page.wait_for_url("**/inventory.html", timeout=10000)
        return True
