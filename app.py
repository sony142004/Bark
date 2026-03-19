"""
Flask web server that provides:
  - A dashboard UI at http://localhost:5000
  - POST /run-agent  → runs the 3-part pipeline and streams results (SSE)
"""

import json
import queue
import threading
import os
from flask import Flask, render_template, request, Response, stream_with_context

from scraper import BarkScraper
from ai_brain import AIBrain, SCORE_THRESHOLD
from pitch_generator import PitchGenerator
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


# ──────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run-agent", methods=["POST"])
def run_agent():
    """
    Accepts optional credentials from the form, runs the agent pipeline,
    and streams progress + results back to the browser via Server-Sent Events.
    """
    data           = request.get_json(silent=True) or {}
    bark_email    = data.get("email",    os.getenv("BARK_EMAIL", ""))
    bark_password = data.get("password", os.getenv("BARK_PASSWORD", ""))
    openai_key    = data.get("api_key",  os.getenv("OPENAI_API_KEY", ""))

    event_queue = queue.Queue()

    def push(event_type: str, payload: dict):
        event_queue.put({"type": event_type, "data": payload})

    def pipeline():
        try:
            # ── PART 1 ──────────────────────────────────────────────────────
            push("log", {"msg": "Part 1 — Scraper launched. Opening browser..."})

            scraper = BarkScraper(email=bark_email or None, password=bark_password or None)
            page    = scraper.start()

            push("log", {"msg": "Browser opened. Attempting login..."})
            logged_in = scraper.login(page)
            if logged_in:
                push("log", {"msg": "Login successful."})
            else:
                push("log", {"msg": "No credentials — skipping login. Using mock data."})

            push("log", {"msg": "Navigating to Buyer Requests / Dashboard..."})
            scraper.go_to_buyer_requests(page)

            push("log", {"msg": "Extracting leads..."})
            leads = scraper.extract_leads(page)
            scraper.stop()

            push("log", {"msg": f"Part 1 complete. Found {len(leads)} lead(s)."})
            push("leads_found", {"count": len(leads)})

            # ── PART 2 ──────────────────────────────────────────────────────
            push("log", {"msg": "Part 2 — AI Brain scoring leads..."})
            brain = AIBrain(api_key=openai_key or None)

            for lead in leads:
                push("log", {"msg": f'Evaluating: "{lead.title}"'})
                brain.evaluate(lead)
                push("lead_scored", {
                    "title":     lead.title,
                    "budget":    lead.budget,
                    "location":  lead.location,
                    "score":     round(lead.score, 2),
                    "reasoning": lead.reasoning,
                })

            push("log", {"msg": "Part 2 complete."})

            # ── PART 3 ──────────────────────────────────────────────────────
            push("log", {"msg": f"Part 3 — Generating pitches for leads with score >= {SCORE_THRESHOLD}..."})
            pitcher = PitchGenerator(api_key=openai_key or None)

            for lead in leads:
                if lead.score >= SCORE_THRESHOLD:
                    push("log", {"msg": f'Drafting pitch for: "{lead.title}"'})
                    pitcher.generate(lead)
                    push("pitch_ready", {
                        "title": lead.title,
                        "pitch": lead.pitch,
                    })

            push("log", {"msg": "All done! Session video saved to videos/ folder."})
            push("done", {"total": len(leads),
                          "high_value": sum(1 for l in leads if l.score >= SCORE_THRESHOLD),
                          "pitches": sum(1 for l in leads if l.pitch)})

        except Exception as e:
            push("error", {"msg": str(e)})

        event_queue.put(None)  # sentinel — stream end

    # Run agent in background thread so SSE can stream
    thread = threading.Thread(target=pipeline, daemon=True)
    thread.start()

    def generate():
        while True:
            item = event_queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"
        yield "data: {\"type\": \"end\"}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000, threaded=True)
