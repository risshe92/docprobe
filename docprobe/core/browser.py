from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class BrowserSession:
    def __init__(self, logger, headless: bool = True):
        self.logger = logger
        self.headless = headless
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self.context = self.browser.new_context()
        self.page = self.new_page()
        return self

    def new_page(self):
        page = self.context.new_page()
        page.set_default_timeout(10000)
        page.set_default_navigation_timeout(120000)
        return page

    def goto(self, url: str, page=None):
        target = page or self.page
        try:
            self.logger.debug("Navigating to %s", url)
            target.goto(url, wait_until="domcontentloaded", timeout=120000)
            target.wait_for_timeout(3000)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"Page load timeout for {url}") from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to load {url}: {exc}") from exc

    def __exit__(self, exc_type, exc, tb):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
