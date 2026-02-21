# Adding a Site Login Handler

Site handlers let the agent log into websites deterministically via Playwright, without sending credentials to the LLM. This guide walks through adding a handler for a new site.

## How it works

When the agent calls `navigate`, `browser.py` calls `try_auto_login(page)` after the page loads. This iterates registered handlers and checks:

1. `matches(url)` — does this handler apply to the current URL? (sync, fast)
2. `is_login_page(page)` — is the page showing a login form? (async, checks DOM)
3. `login(page)` — fill credentials and submit (async)

If login succeeds, the navigate tool result includes a status line like `[Auto-login completed for SiteName]` so the LLM knows it can proceed without manual login.

## Steps

### 1. Create the handler module

Create `src/web_automator/sites/your_site.py`. Use `saucedemo.py` as a template:

```python
"""Deterministic login handler for yoursite.com."""

from __future__ import annotations

import os

from playwright.async_api import Page

from .base import SiteHandler


class YourSiteHandler(SiteHandler):

    @property
    def site_name(self) -> str:
        return "YourSite"

    def matches(self, url: str) -> bool:
        return "yoursite.com" in url

    async def is_login_page(self, page: Page) -> bool:
        # Check for a login-specific element
        return await page.locator("#login-form").count() > 0

    async def login(self, page: Page) -> bool:
        username = os.getenv("YOURSITE_USERNAME")
        password = os.getenv("YOURSITE_PASSWORD")
        if not username or not password:
            return False  # graceful fallback — LLM handles login

        await page.locator("#username").fill(username)
        await page.locator("#password").fill(password)
        await page.locator("button[type=submit]").click()
        await page.wait_for_url("**/dashboard", timeout=10000)
        return True
```

Key points:
- `matches()` should be a fast string check — no network I/O.
- `is_login_page()` should check for a login-specific DOM element to avoid false positives.
- `login()` must return `False` if credentials are missing, so the agent falls back to LLM-driven login.
- Use `wait_for_url()` or `wait_for_selector()` after clicking submit to confirm navigation completed.

### 2. Register the handler

In `src/web_automator/sites/__init__.py`, import and add your handler to `_HANDLERS`:

```python
from .saucedemo import SauceDemoHandler
from .your_site import YourSiteHandler

_HANDLERS = [
    SauceDemoHandler(),
    YourSiteHandler(),
]
```

### 3. Add credentials to `.env.example`

```
# YourSite credentials (for auto-login)
YOURSITE_USERNAME=
YOURSITE_PASSWORD=
```

Then add actual values to your local `.env`.

### 4. Test it

```bash
python -m web_automator --verbose "go to yoursite.com and list the dashboard items"
```

In the verbose output, you should see the navigate result include:
```
[Auto-login completed for YourSite — now at https://yoursite.com/dashboard, title='Dashboard']
```

## Reference

| File | Purpose |
|---|---|
| `src/web_automator/sites/base.py` | `SiteHandler` ABC — defines the interface |
| `src/web_automator/sites/saucedemo.py` | Reference implementation |
| `src/web_automator/sites/__init__.py` | Handler registry + `try_auto_login()` |
| `src/web_automator/browser.py` | Calls `try_auto_login()` in `_navigate()` |
