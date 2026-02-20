import pytest
from playwright.sync_api import expect

# @pytest.mark.usefixtures("setup_playwright")
def test_swag_labs_happy_path_add_to_cart(setup_playwright) -> None:
    page = setup_playwright
    # Navigate to login
    page.goto("https://www.saucedemo.com/")

    # Login
    page.locator("[data-test='username']").fill("standard_user")
    page.locator("[data-test='password']").fill("secret_sauce")
    page.locator("[data-test='login-button']").click()

    # Verify inventory page
    expect(page.locator("[data-test='title']")).to_have_text("Products")
    expect(page.locator("[data-test='inventory-list']")).to_be_visible()

    # Add a few items to the cart
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()
    page.locator("[data-test='add-to-cart-sauce-labs-bike-light']").click()
    page.locator("[data-test='add-to-cart-sauce-labs-bolt-t-shirt']").click()

    # Open the cart
    page.locator("[data-test='shopping-cart-link']").click()

    # Verify cart page and contents
    expect(page.locator("[data-test='title']")).to_have_text("Your Cart")
    expect(page.locator(".cart_item")).to_have_count(3)
    expect(page.locator("[data-test='shopping-cart-badge']")).to_have_text("3")

    # Verify the expected item names are present
    expected_names = [
        "Sauce Labs Backpack",
        "Sauce Labs Bike Light",
        "Sauce Labs Bolt T-Shirt",
    ]
    for name in expected_names:
        expect(page.locator(".cart_item .inventory_item_name", has_text=name)).to_be_visible()

    # Remove one item and verify counts update
    page.locator("[data-test='remove-sauce-labs-bike-light']").click()
    expect(page.locator(".cart_item")).to_have_count(2)
    expect(page.locator("[data-test='shopping-cart-badge']")).to_have_text("2")

    # Continue shopping and verify we are back on inventory
    page.locator("[data-test='continue-shopping']").click()
    expect(page.locator("[data-test='inventory-list']")).to_be_visible()