from playwright.sync_api import sync_playwright


def main() -> None:
    """
    Simple Playwright demo.

    Opens a Chromium browser, goes to example.com, prints the page title,
    then closes the browser.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False = show browser window
        page = browser.new_page()
        page.goto("https://example.com")
        print("Page title is:", page.title())
        browser.close()


if __name__ == "__main__":
    main()

