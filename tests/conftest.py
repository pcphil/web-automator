import pytest
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

@pytest.fixture(scope="session")
def setup_playwright():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        yield page
