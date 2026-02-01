import groq
from config import GROQ_API_KEY, GROQ_MODEL

client = groq.Groq(api_key=GROQ_API_KEY)

def generate_cold_email(business_name: str, niche: str, city: str, snippet: str) -> dict:
    prompt = f"""You are Kunal from Devark Studios (https://devark.studio), a web design agency that builds high-converting websites for brands.
You have worked with Shark Tank brands like Kunafa Mafias.

Write a short, professional, personalized cold email to a local business that does not have a website yet (or needs an upgrade).
Offer to build them a professional website that establishes credibility and drives customers.

Business details:
- Name: {business_name}
- Type/Niche: {niche}
- City: {city}
- About them (from search): {snippet}

Rules:
- Keep it under 150 words
- Tone: Professional, confident, but helpful
- Mention: "We build websites for brands" and reference "Shark Tank brands like Kunafa Mafias" to establish authority
- Mention their specific business name to show research
- Value Prop: "We can build a premium website that makes {business_name} look professional."
- Call to Action: "Reply to this email if you're interested in connecting further."
- Do NOT use bullet points or numbered lists
- Sign off as: Kunal, Devark Studios (https://devark.studio)

Output ONLY two things, separated by a line that says exactly "---BODY---":
First line: the subject line
Then ---BODY---
Then: the email body

Do not add any extra commentary."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    if "---BODY---" in raw:
        parts = raw.split("---BODY---", 1)
        subject = parts[0].strip()
        body    = parts[1].strip()
    else:
        lines   = raw.split("\n", 1)
        subject = lines[0].strip()
        body    = lines[1].strip() if len(lines) > 1 else raw

    print(f"[AI] Generated email for '{business_name}'")
    print(f"     Subject: {subject}")
    return {"subject": subject, "body": body}


def classify_reply(reply_text: str, business_name: str) -> str:
    prompt = f"""A freelancer sent a cold email to a business called "{business_name}".
The business replied with this message:

---
{reply_text}
---

Classify this reply into EXACTLY one of these three categories:
- interested        (they want to talk, ask for details, or say yes)
- not_interested    (they decline, say no, or ignore the offer)
- needs_followup    (ambiguous, they asked a question, or need more info)

Respond with ONLY the single word category. Nothing else."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.0,
    )

    classification = response.choices[0].message.content.strip().lower()

    valid = {"interested", "not_interested", "needs_followup"}
    if classification not in valid:
        classification = "needs_followup"

    print(f"[AI] Reply from '{business_name}' classified as: {classification}")
    return classification