"""
===================================================
  PART 3 — PITCH GENERATOR
===================================================
  For leads with score > 0.8:
    → Generates a personalized 3-paragraph proposal
    → References ≥ 2 specific details from the request
    → Tone: professional, expert, and human
===================================================
"""

from openai import OpenAI


class PitchGenerator:
    """
    Generates a personalized outreach pitch for a high-scoring lead.

    Rules enforced by the LLM prompt:
      1. Exactly 3 paragraphs.
      2. Must reference at least 2 specific details from the buyer's request.
      3. Professional, confident, and empathetic tone.
    """

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key) if api_key else None

    def generate(self, lead) -> None:
        """
        Generate a pitch for the given Lead object in-place.
        Updates lead.pitch.
        """
        print(f"  [PITCH GEN] Drafting pitch for: '{lead.title}'")

        if not self.client:
            lead.pitch = self._fallback_pitch(lead)
            return

        prompt = self._build_prompt(lead)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a world-class sales writer who crafts "
                            "highly personalized, persuasive pitches that win contracts."
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            )
            lead.pitch = response.choices[0].message.content.strip()

        except Exception as e:
            print(f"  [PITCH GEN] Error generating pitch: {e}")
            lead.pitch = f"Pitch generation failed: {e}"

    @staticmethod
    def _build_prompt(lead) -> str:
        return f"""
Write a personalized outreach pitch for the following buyer request.

Buyer's Request:
  Title       : {lead.title}
  Description : {lead.description}
  Budget      : {lead.budget}
  Location    : {lead.location}

Hard Requirements:
  1. Exactly 3 paragraphs (no more, no less).
  2. Reference at LEAST two specific details from the description above
     (e.g. the number of products, tech stack mentioned, timeline, etc.)
     to show you actually read their request.
  3. Tone: Professional, expert, and friendly — not robotic or generic.
  4. End with a confident call-to-action inviting them to schedule a call.

Do NOT add subject lines, signatures, or any text outside the 3 paragraphs.
"""

    @staticmethod
    def _fallback_pitch(lead) -> str:
        """A pre-written mock pitch used when there is no API key."""
        return (
            f"I came across your request for '{lead.title}' and I'm confident "
            f"we'd be a great fit. Your project aligns perfectly with our "
            f"core specialization in high-end web development.\n\n"
            f"Looking at your description, two things stood out immediately: "
            f"the specific technical scope of the work and the clear budget "
            f"of {lead.budget}, which tells me you are serious about quality. "
            f"Our team has delivered similar projects with measurable results.\n\n"
            f"I'd love to schedule a 20-minute discovery call to discuss your "
            f"requirements in detail and share a few ideas we think could add "
            f"real value. Would this week work for you?"
        )
