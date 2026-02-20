# Skill: Playwright Test Generation

## When to use
Use this playbook whenever the task asks you to generate, create, or write a Playwright test for a web page.

## Workflow

1. **Navigate** to the target page with the `navigate` tool.
2. **Get the raw HTML** — call `get_html` (no selector) to retrieve the full page source.
   - If you only care about a specific section (e.g. a login form), pass a CSS selector: `get_html(selector="#login-form")`.
3. **Inspect the HTML** to identify reliable locators. Use this priority order:
   1. `data-testid` attribute → `[data-testid="submit-btn"]`
   2. `aria-label` / `role` → `getByRole('button', { name: 'Submit' })`
   3. `name` attribute → `[name="email"]`
   4. `id` → `#username`
   5. Stable CSS class (avoid generated class names like `.css-1x2y3z`)
   6. Visible text (last resort) → `getByText('Sign in')`
4. **Generate the test** using the pytest-playwright structure below.
5. **Write the file** — call `write_test(filename="test_<page>.py", content=<generated code>)`.
6. **Report** the file path returned by `write_test` in your `done` result.

## Test File Template

```python
import pytest
from playwright.sync_api import Page, expect


def test_<page_name>(page: Page) -> None:
    # Navigate
    page.goto("https://example.com")

    # Assert page loaded
    expect(page).to_have_title("Example Domain")

    # Interact with elements
    # page.get_by_role("button", name="Submit").click()
    # page.locator("[data-testid='email']").fill("user@example.com")

    # Assert outcomes
    # expect(page.locator(".success-message")).to_be_visible()
    # expect(page.locator("h1")).to_have_text("Welcome")
```

## Locator Cheat Sheet

| Scenario | Playwright locator |
|---|---|
| By test ID | `page.get_by_test_id("submit")` |
| By role + name | `page.get_by_role("button", name="Log in")` |
| By label | `page.get_by_label("Email address")` |
| By placeholder | `page.get_by_placeholder("Search…")` |
| By CSS | `page.locator("#main-nav .logo")` |
| By text | `page.get_by_text("Accept cookies")` |
| Nth match | `page.locator("li.result").nth(0)` |

## Assertion Cheat Sheet

| Check | Assertion |
|---|---|
| Element visible | `expect(locator).to_be_visible()` |
| Element hidden | `expect(locator).to_be_hidden()` |
| Text content | `expect(locator).to_have_text("exact text")` |
| Partial text | `expect(locator).to_contain_text("partial")` |
| Attribute value | `expect(locator).to_have_attribute("href", "/home")` |
| Input value | `expect(locator).to_have_value("my@email.com")` |
| Page title | `expect(page).to_have_title("My App")` |
| URL | `expect(page).to_have_url("https://example.com/dashboard")` |
| Element count | `expect(locator).to_have_count(5)` |

## Tips
- Always call `get_html` before writing selectors — never guess from a URL alone.
- Keep each test function focused on a single user flow.
- Add a `conftest.py` with `base_url` fixture if generating tests for an app with many pages.
- Generated tests go into `generated_tests/` — the agent does not run them automatically.
