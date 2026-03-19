"""
===================================================
  PART 2 — AI BRAIN (LLM Scoring)
===================================================
  Reads each lead
  Sends it to GPT-4o with a clear prompt
  Gets back a score from 0.0 → 1.0
  Decides whether the lead is worth pursuing
===================================================
"""

import json
from openai import OpenAI


# ─────────────────────────────────────────────
#  Ideal Customer Profile (ICP)
#  Change this to match YOUR target clients.
# ─────────────────────────────────────────────
IDEAL_CUSTOMER_PROFILE = """
Our Ideal Customer Profile (ICP):
  • Project Type : High-end Web Development, E-commerce, SaaS, or Custom App builds.
  • Budget       : $2,000 minimum. Higher is better.
  • Client Type  : Serious business owners, funded startups, or established companies.
  • Not a Match  : Tiny bug fixes, simple WordPress edits, or budgets under $500.
"""

SCORE_THRESHOLD = 0.8   # leads above this get a pitch


# ─────────────────────────────────────────────
#  AI Brain Class
# ─────────────────────────────────────────────
class AIBrain:
    """
    Sends lead data to an LLM and receives:
      - score     : float (0.0 = terrible match, 1.0 = perfect match)
      - reasoning : why that score was given
    """

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key) if api_key else None

    def evaluate(self, lead) -> None:
        """
        Score the given Lead object in-place.
        Updates lead.score and lead.reasoning.
        """
        print(f"  [AI BRAIN] Evaluating: '{lead.title}'")

        if not self.client:
            # No API key — use a simulated score so the pipeline still runs
            lead.score = 0.9
            lead.reasoning = "Simulated score (no API key). Matches ICP based on title/budget."
            return

        prompt = self._build_prompt(lead)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert sales strategist. "
                            "Your job is to score service leads based on our ICP. "
                            "Always respond with valid JSON only."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            lead.score     = float(result.get("score", 0.0))
            lead.reasoning = result.get("reasoning", "No reasoning returned.")

        except Exception as e:
            print(f"  [AI BRAIN] Error during evaluation: {e}")
            lead.score     = 0.0
            lead.reasoning = f"Evaluation failed: {e}"

    @staticmethod
    def _build_prompt(lead) -> str:
        return f"""
Evaluate this service lead against our Ideal Customer Profile.

{IDEAL_CUSTOMER_PROFILE}

Lead Details:
  Title       : {lead.title}
  Description : {lead.description}
  Budget      : {lead.budget}
  Location    : {lead.location}

Return a JSON object with exactly two keys:
  "score"     : a float between 0.0 (no match) and 1.0 (perfect match)
  "reasoning" : a 1–2 sentence explanation of the score
"""
