"""Abstract base class for deterministic site login handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from playwright.async_api import Page


class SiteHandler(ABC):
    """Handles automatic login for a specific website."""

    @property
    @abstractmethod
    def site_name(self) -> str:
        """Human-readable site name (e.g. 'SauceDemo')."""

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Return True if this handler applies to the given URL (fast, sync)."""

    @abstractmethod
    async def is_login_page(self, page: Page) -> bool:
        """Return True if the page is currently showing a login form."""

    @abstractmethod
    async def login(self, page: Page) -> bool:
        """Fill credentials and submit. Return True on success, False on failure."""
