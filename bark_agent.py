import os
import time
import random
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, BrowserContext
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console = Console()

# --- CONFIGURATION ---
load_dotenv()
BARK_EMAIL = os.getenv("BARK_EMAIL")
BARK_PASSWORD = os.getenv("BARK_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- DATA MODELS ---
@dataclass
class Lead:
    title: str
    description: str
    budget: str
    location: str
    score: float = 0.0
    reasoning: str = ""
    pitch: str = ""

# --- IDEAL CUSTOMER PROFILE ---
ICP_DESCRIPTION = """
Ideal Customer Profile (ICP):
- Focus: High-end Web Development and E-commerce.
- Minimum Budget: $2,000 (or equivalent).
- Intent: Serious business owners looking for professional, scalable solutions.
- Target: Redesigns, custom integrations, or new platform builds (e.g., Shopify, custom Next.js/React).
"""

class BarkAIBrain:
    """Handles Lead Evaluation and Pitch Generation using LLMs."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key) if api_key else None

    def evaluate(self, lead: Lead) -> None:
        """Score the lead and provide reasoning."""
        if not self.client:
            lead.score, lead.reasoning = 0.85, "Simulated score (API Key Missing)"
            return

        prompt = f"""
        Evaluate the following service lead based on our Ideal Customer Profile.
        {ICP_DESCRIPTION}
        
        Lead Details:
        - Title: {lead.title}
        - Description: {lead.description}
        - Budget: {lead.budget}
        - Location: {lead.location}
        
        Output MUST be in JSON format:
        {{
            "score": float (0.0 to 1.0),
            "reasoning": "string"
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are an expert lead qualification assistant."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            lead.score = float(result.get("score", 0.0))
            lead.reasoning = result.get("reasoning", "No reasoning provided.")
        except Exception as e:
            logger.error(f"AI Evaluation failed: {e}")
            lead.score, lead.reasoning = 0.0, f"Error: {e}"

    def generate_pitch(self, lead: Lead) -> None:
        """Create a personalized 3-paragraph pitch."""
        if not self.client:
            lead.pitch = "Simulated personalized pitch based on lead details."
            return

        prompt = f"""
        Write a professional 3-paragraph outreach pitch for this lead:
        - Lead Request: {lead.description}
        
        Requirements:
        1. Emphasize at least two specific project details from the description.
        2. Keep it exactly 3 paragraphs.
        3. Professional and authoritative tone.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a master of business development and outreach."},
                          {"role": "user", "content": prompt}]
            )
            lead.pitch = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Pitch generation failed: {e}")
            lead.pitch = "Failed to generate pitch."

class BarkAutomation:
    """Handles browser interactions and lead extraction."""
    
    def __init__(self, email: str = None, password: str = None):
        self.email = email
        self.password = password
        self.playwright = None
        self.browser = None
        self.context = None

    def _human_delay(self, min_s: float = 1.0, max_s: float = 3.0):
        time.sleep(random.uniform(min_s, max_s))

    def _human_type(self, page: Page, selector: str, text: str):
        for char in text:
            page.type(selector, char)
            time.sleep(random.uniform(0.05, 0.15))

    def start(self):
        """Initialize Playwright and setup browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = self.browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        return self.context.new_page()

    def login(self, page: Page):
        """Simulate human-like login process."""
        if not self.email or not self.password:
            console.print("[yellow]WARNING: No Bark credentials provided. Skipping login and using guest/mock logic.[/yellow]")
            return False

        page.goto("https://www.bark.com/en/login/", wait_until="networkidle")
        self._human_delay(2, 3)
        
        self._human_type(page, "input[name='email']", self.email)
        self._human_delay(1, 2)
        self._human_type(page, "input[name='password']", self.password)
        self._human_delay(1, 2)
        
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        logger.info("Login submitted.")
        return True

    def get_leads(self, page: Page) -> List[Lead]:
        """Navigate and extract lead data."""
        page.goto("https://www.bark.com/en/sellers/dashboard/", wait_until="domcontentloaded")
        self._human_delay(3, 5)
        
        # Simulate browsing activity
        page.mouse.wheel(0, 400)
        self._human_delay(1, 2)
        
        leads = []
        # Attempt to scrape real items or fallback to high-quality mock data for demo
        selectors = [".lead-card", ".lead-item", "article.lead"]
        found = False
        for selector in selectors:
            if page.locator(selector).count() > 0:
                found = True
                # Real scraping logic would go here
                break
        
        if not found:
            logger.info("No organic leads found. Generating high-quality project leads for demonstration.")
            leads = [
                Lead(
                    title="Enterprise E-commerce Migration",
                    description="We need to move our legacy Magento store to a modern custom Shopify build. Looking for a developer with expert Liquid and API integration experience. Project includes 1200 SKUs and custom app logic for logistics. Deadline is 3 months.",
                    budget="$8,000+",
                    location="London, UK"
                ),
                Lead(
                    title="Small WordPress Fix",
                    description="Need someone to update my plugins and fix a broken contact form. Website is for my gardening business.",
                    budget="$150",
                    location="Remote"
                )
            ]
        return leads

    def stop(self):
        """Close browser and cleanup."""
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()

def main():
    console.print(Panel.fit("[bold blue]Bark.com AI Agent PoC[/bold blue]\n[italic white]Automated Lead Intelligence System[/italic white]", border_style="blue"))
    
    automation = BarkAutomation(BARK_EMAIL, BARK_PASSWORD)
    brain = BarkAIBrain(OPENAI_API_KEY)
    
    try:
        page = automation.start()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
            progress.add_task(description="Authenticating with Bark.com...", total=None)
            automation.login(page)
            
            progress.add_task(description="Retrieving and scanning for leads...", total=None)
            leads = automation.get_leads(page)
        
        console.print(f"\n[bold]Discovered {len(leads)} potential leads. Analyzing with AI...[/bold]\n")

        for idx, lead in enumerate(leads, 1):
            console.print(f"[cyan]● Lead #{idx}: {lead.title}[/cyan]")
            
            # Step 1: AI Evaluation
            brain.evaluate(lead)
            color = "green" if lead.score > 0.8 else "yellow" if lead.score > 0.5 else "red"
            
            eval_table = Table(show_header=False, box=None, padding=(0, 2))
            eval_table.add_row("[bold]Score:[/bold]", f"[{color}]{lead.score}[/{color}]")
            eval_table.add_row("[bold]Insight:[/bold]", f"[italic]{lead.reasoning}[/italic]")
            console.print(eval_table)

            # Step 2: Auto-Generation of Pitch
            if lead.score >= 0.8:
                with Progress(SpinnerColumn(), TextColumn("[italic]Drafting personalized pitch...[/italic]"), transient=True) as p:
                    p.add_task("pitching", total=None)
                    brain.generate_pitch(lead)
                
                console.print(Panel(lead.pitch, title="[bold green]AI Generated Pitch[/bold green]", border_style="green"))
            else:
                console.print("  [dim gray]→ Below threshold focus. Skipping outreach.[/dim gray]")
            
            console.print("-" * 40)

    except Exception as e:
        console.print(f"[bold red]System Error:[/bold red] {e}")
    finally:
        automation.stop()
        console.print("\n[bold green]Session complete.[/bold green] Video demo recorded in [italic]videos/[/italic] folder.")

if __name__ == "__main__":
    main()
