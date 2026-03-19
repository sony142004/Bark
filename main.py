"""
===================================================
  MAIN -- Orchestrator
===================================================
  Ties all 3 parts together:

    Part 1  BarkScraper     (scraper.py)
    Part 2  AIBrain         (ai_brain.py)
    Part 3  PitchGenerator  (pitch_generator.py)

  Run:  python main.py
===================================================
"""
import sys
import io
# Fix Windows terminal encoding so Rich output works correctly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ── Import the 3 parts ────────────────────────
from scraper import BarkScraper
from ai_brain import AIBrain, SCORE_THRESHOLD
from pitch_generator import PitchGenerator

# ── Load credentials ──────────────────────────
load_dotenv()
BARK_EMAIL    = os.getenv("BARK_EMAIL")
BARK_PASSWORD = os.getenv("BARK_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

console = Console()


def print_lead_result(lead, index: int) -> None:
    """Pretty-print a single lead's score and optional pitch."""

    # ── Score colour ──────────────────────────
    if lead.score >= SCORE_THRESHOLD:
        score_style = "bold green"
        badge       = "[HIGH VALUE]"
    elif lead.score >= 0.5:
        score_style = "bold yellow"
        badge       = "[MEDIUM]"
    else:
        score_style = "bold red"
        badge       = "[LOW VALUE]"

    # ── Evaluation summary table ──────────────
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="dim", width=14)
    table.add_column("Value")

    table.add_row("Title",    lead.title)
    table.add_row("Budget",   lead.budget)
    table.add_row("Location", lead.location)
    table.add_row("Score",    f"[{score_style}]{lead.score:.2f}  {badge}[/{score_style}]")
    table.add_row("Insight",  f"[italic]{lead.reasoning}[/italic]")

    console.print(Panel(table, title=f"[bold cyan]Lead #{index}[/bold cyan]", border_style="cyan"))

    # ── Pitch (only if score > threshold) ─────
    if lead.pitch:
        console.print(
            Panel(
                lead.pitch,
                title="[bold green]AI-Generated Pitch[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
        )
    else:
        console.print("  [dim]Score below threshold. No pitch generated.[/dim]\n")


def main():
    # ── Header ────────────────────────────────
    console.print(
        Panel.fit(
            "[bold blue]Bark.com AI Lead Agent[/bold blue]\n"
            "[white]Part 1: Scraper  -->  Part 2: AI Brain  -->  Part 3: Pitch Generator[/white]",
            border_style="blue",
            padding=(1, 4)
        )
    )

    # ════════════════════════════════════════
    #  PART 1 — SCRAPER
    # ════════════════════════════════════════
    console.rule("[bold]Part 1 -- Scraper[/bold]")
    scraper = BarkScraper(email=BARK_EMAIL, password=BARK_PASSWORD)

    try:
        page = scraper.start()
        scraper.login(page)
        scraper.go_to_buyer_requests(page)
        leads = scraper.extract_leads(page)
    finally:
        scraper.stop()   # always close the browser

    console.print(f"\n[bold]Found {len(leads)} lead(s) to process.[/bold]\n")

    # ════════════════════════════════════════
    #  PART 2 — AI BRAIN
    # ════════════════════════════════════════
    console.rule("[bold]Part 2 -- AI Brain (Scoring)[/bold]")
    brain = AIBrain(api_key=OPENAI_API_KEY)

    for lead in leads:
        brain.evaluate(lead)          # updates lead.score & lead.reasoning in-place

    # ════════════════════════════════════════
    #  PART 3 — PITCH GENERATOR
    # ════════════════════════════════════════
    console.rule("[bold]Part 3 -- Pitch Generator[/bold]")
    pitcher = PitchGenerator(api_key=OPENAI_API_KEY)

    for lead in leads:
        if lead.score >= SCORE_THRESHOLD:
            pitcher.generate(lead)    # updates lead.pitch in-place

    # ════════════════════════════════════════
    #  RESULTS
    # ════════════════════════════════════════
    console.rule("[bold]Results[/bold]")

    for i, lead in enumerate(leads, start=1):
        print_lead_result(lead, i)

    # ── Summary ───────────────────────────────
    high_value = [l for l in leads if l.score >= SCORE_THRESHOLD]
    console.print(
        Panel(
            f"[bold]Total leads processed:[/bold] {len(leads)}\n"
            f"[bold green]High-value leads (score >= {SCORE_THRESHOLD}):[/bold green] {len(high_value)}\n"
            f"[bold]Pitches generated:[/bold] {sum(1 for l in leads if l.pitch)}\n\n"
            f"[dim]Session video saved to:[/dim] [italic]videos/[/italic]",
            title="[bold]Session Summary[/bold]",
            border_style="blue"
        )
    )


if __name__ == "__main__":
    main()
