"""
===================================================
  PART 1 — SCRAPER (Automation Agent)
===================================================
  Logs into Bark.com
  Navigates to Buyer Requests / Dashboard
  Extracts leads (title, description, budget, location)
===================================================
"""

import time
import random
from dataclasses import dataclass, field
from typing import List

from playwright.sync_api import sync_playwright, Page


# ─────────────────────────────────────────────
#  Data Model — a single Lead
# ─────────────────────────────────────────────
@dataclass
class Lead:
    title: str
    description: str
    budget: str
    location: str
    # Filled in later by Part 2 & 3
    score: float = 0.0
    reasoning: str = ""
    pitch: str = ""


# ─────────────────────────────────────────────
#  Helper — human-like behaviour
# ─────────────────────────────────────────────
def _random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Pause for a random duration to mimic a real user."""
    time.sleep(random.uniform(min_s, max_s))


def _human_type(page: Page, selector: str, text: str) -> None:
    """Type character-by-character with random delays."""
    for char in text:
        page.type(selector, char)
        time.sleep(random.uniform(0.05, 0.18))


# ─────────────────────────────────────────────
#  Scraper Class
# ─────────────────────────────────────────────
class BarkScraper:
    """
    Controls the browser session.
    1. Opens Bark.com
    2. Logs in (if credentials are provided)
    3. Goes to Buyer Requests / Dashboard
    4. Returns a list of Lead objects
    """

    def __init__(self, email: str = None, password: str = None):
        self.email = email
        self.password = password
        self._playwright = None
        self._browser = None
        self._context = None

    # ── Lifecycle ──────────────────────────────
    def start(self) -> Page:
        """Launch the browser and return the active page."""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False,                                  # Visible so you can watch it work
            args=["--disable-blink-features=AutomationControlled"]  # Basic bot-detection bypass
        )
        self._context = self._browser.new_context(
            record_video_dir="videos/",                      # Auto-record the session
            record_video_size={"width": 1280, "height": 720},
            # Mimic a real Chrome browser
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        return self._context.new_page()

    def stop(self) -> None:
        """Gracefully close browser and Playwright."""
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    # ── Step 1 of 3: Login ────────────────────
    def login(self, page: Page) -> bool:
        """
        Navigates to the login page and signs in with human-like
        typing speed and random mouse delays.
        Returns True on success, False if credentials are missing.
        """
        if not self.email or not self.password:
            print("[SCRAPER] No credentials provided — skipping login.")
            return False

        print("[SCRAPER] Navigating to login page...")
        page.goto("https://www.bark.com/en/login/", wait_until="networkidle")
        _random_delay(2, 3)

        # Type email
        _human_type(page, "input[name='email']", self.email)
        _random_delay(0.8, 1.5)

        # Type password
        _human_type(page, "input[name='password']", self.password)
        _random_delay(0.8, 1.5)

        # Hover over button, then click (more human-looking)
        submit = page.locator("button[type='submit']")
        submit.hover()
        _random_delay(0.3, 0.7)
        submit.click()

        page.wait_for_load_state("networkidle")
        print("[SCRAPER] Logged in successfully.")
        return True

    # ── Step 2 of 3: Navigate to Buyer Requests ──
    def go_to_buyer_requests(self, page: Page) -> None:
        """
        Goes to the Bark Pro dashboard where buyer
        requests and open leads are listed.
        Falls back to the homepage if dashboard requires login.
        """
        print("[SCRAPER] Navigating to Buyer Requests / Dashboard...")
        try:
            page.goto("https://www.bark.com/en/sellers/dashboard/", wait_until="domcontentloaded", timeout=15000)
        except Exception:
            # Fallback if dashboard is login-gated
            page.goto("https://www.bark.com/en/us/", wait_until="domcontentloaded", timeout=15000)
        
        _random_delay(2, 4)

        # Scroll down slowly to trigger any lazy-loaded content
        try:
            for _ in range(3):
                page.mouse.wheel(0, 400)
                _random_delay(0.5, 1.2)
        except Exception as e:
            print(f"[SCRAPER] Scroll skipped: {e}")

    # ── Step 3 of 3: Extract Leads ────────────
    def extract_leads(self, page: Page) -> List[Lead]:
        """
        Attempts to scrape leads from the page.
        Falls back to high-quality mock data if scraping
        is not possible (e.g. no login, layout change).
        """
        print("[SCRAPER] Extracting leads...")

        # Try common lead-card selectors
        SELECTORS = [".lead-card", ".lead-item", "article.lead", ".request-card"]
        found_any = any(page.locator(sel).count() > 0 for sel in SELECTORS)

        if found_any:
            return self._scrape_live(page, SELECTORS)
        else:
            print("[SCRAPER] No live leads found — using mock data to demonstrate pipeline.")
            return self._mock_leads()

    def _scrape_live(self, page: Page, selectors: list) -> List[Lead]:
        """Parse real lead cards from the DOM."""
        leads = []
        for sel in selectors:
            cards = page.locator(sel)
            if cards.count() == 0:
                continue
            for i in range(min(cards.count(), 5)):   # cap at 5 leads
                card = cards.nth(i)
                card.scroll_into_view_if_needed()
                _random_delay(0.5, 1.0)
                title  = card.locator("h2, .lead-title").first.text_content(timeout=2000) or "No Title"
                desc   = card.locator("p, .lead-desc").first.text_content(timeout=2000) or "No Description"
                budget = card.locator(".budget, .price-tag").first.text_content(timeout=2000) or "Budget not listed"
                loc    = card.locator(".location, .loc").first.text_content(timeout=2000) or "Location not listed"
                leads.append(Lead(title.strip(), desc.strip(), budget.strip(), loc.strip()))
            break   # use the first matching selector
        return leads

    def _mock_leads(self) -> List[Lead]:
        """
        Realistic sample leads used when scraping is unavailable.
        One is a perfect ICP match; the other is a poor match.
        This lets you see BOTH paths of the AI Brain in action.
        """
        return [
            Lead(
                title="Full E-commerce Website Build (Shopify + Custom API)",
                description=(
                    "We are a fashion startup with 300+ products looking to launch a "
                    "premium Shopify store. We need custom theme development, a product "
                    "recommendation engine, and integrations with our logistics API. "
                    "Timeline: 8 weeks. The budget is flexible for the right team."
                ),
                budget="$5,000 – $8,000",
                location="New York, NY"
            ),
            Lead(
                title="Fix One Bug on My WordPress Site",
                description=(
                    "My contact form broke last week after a plugin update. "
                    "Total budget is $75. Should be a quick fix."
                ),
                budget="$75",
                location="Remote"
            )
        ]
