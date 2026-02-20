"""Playwright browser wrapper and tool executor."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)


@dataclass
class ToolResult:
    success: bool
    output: str  # text result or base64 image
    is_image: bool = False
    error: str | None = None


class BrowserSession:
    """Manages a single Playwright browser session."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self._context.new_page()

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self.page = None
        self._playwright = None

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Dispatch a tool call to the corresponding browser action."""
        if self.page is None:
            return ToolResult(success=False, output="", error="Browser not started")

        try:
            match name:
                case "navigate":
                    return await self._navigate(arguments["url"])
                case "click":
                    return await self._click(arguments["selector"])
                case "type":
                    return await self._type(arguments["selector"], arguments["text"])
                case "scroll":
                    return await self._scroll(
                        arguments["direction"],
                        arguments.get("amount", 500),
                    )
                case "wait_for":
                    return await self._wait_for(
                        arguments["selector"],
                        arguments.get("timeout", 10000),
                    )
                case "screenshot":
                    return await self._screenshot()
                case "get_page_content":
                    return await self._get_page_content()
                case "get_html":
                    return await self._get_html(arguments.get("selector"))
                case "extract":
                    return await self._extract(arguments["description"])
                case "done":
                    return ToolResult(success=True, output=arguments["result"])
                case _:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Unknown tool: {name!r}",
                    )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))

    # ------------------------------------------------------------------
    # Individual actions
    # ------------------------------------------------------------------

    async def _navigate(self, url: str) -> ToolResult:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        elif url.startswith("http://"):
            url = "https://" + url[7:]  # upgrade plain HTTP to HTTPS
        response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        status = response.status if response else "unknown"
        title = await self.page.title()
        return ToolResult(
            success=True,
            output=f"Navigated to {url} (status={status}, title={title!r})",
        )

    async def _click(self, selector: str) -> ToolResult:
        # Try CSS selector first; fall back to visible text
        try:
            await self.page.locator(selector).first.click(timeout=5000)
        except Exception:
            await self.page.get_by_text(selector).first.click(timeout=5000)
        return ToolResult(success=True, output=f"Clicked {selector!r}")

    async def _type(self, selector: str, text: str) -> ToolResult:
        locator = self.page.locator(selector).first
        await locator.click()
        await locator.fill(text)
        return ToolResult(success=True, output=f"Typed {text!r} into {selector!r}")

    async def _scroll(self, direction: str, amount: int) -> ToolResult:
        delta = amount if direction == "down" else -amount
        await self.page.evaluate(f"window.scrollBy(0, {delta})")
        return ToolResult(success=True, output=f"Scrolled {direction} by {amount}px")

    async def _wait_for(self, selector: str, timeout: int) -> ToolResult:
        await self.page.wait_for_selector(selector, timeout=timeout)
        return ToolResult(success=True, output=f"Element {selector!r} appeared")

    async def _screenshot(self) -> ToolResult:
        data = await self.page.screenshot(type="png", full_page=False)
        encoded = base64.b64encode(data).decode()
        return ToolResult(success=True, output=encoded, is_image=True)

    async def _get_page_content(self) -> ToolResult:
        title = await self.page.title()
        url = self.page.url
        # Extract visible text via JS (strip scripts/styles)
        text = await self.page.evaluate("""() => {
            const clone = document.body.cloneNode(true);
            for (const el of clone.querySelectorAll('script, style, noscript')) {
                el.remove();
            }
            return clone.innerText || clone.textContent || '';
        }""")
        # Truncate to avoid overwhelming the LLM
        text = text.strip()[:8000]
        return ToolResult(
            success=True,
            output=f"URL: {url}\nTitle: {title}\n\n{text}",
        )

    async def _get_html(self, selector: str | None = None) -> ToolResult:
        if selector:
            html = await self.page.locator(selector).first.inner_html()
        else:
            html = await self.page.content()
        return ToolResult(success=True, output=html[:60000])

    async def _extract(self, description: str) -> ToolResult:
        content = await self._get_page_content()
        # Return the full content; the LLM will do the extraction from its context
        return ToolResult(
            success=True,
            output=f"Page content for extraction ({description!r}):\n{content.output}",
        )


def create_browser_session() -> BrowserSession:
    headless_env = os.getenv("HEADLESS", "true").lower()
    headless = headless_env not in ("false", "0", "no")
    return BrowserSession(headless=headless)
