"""
jd_agent.py — Agent A backend (SmartSMBAI)
Two-call approach: structured JSON first, plain-text full_jd second.
Eliminates unterminated string JSON errors from multi-line prose in JSON.
"""
import os, json, re
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic
from database import _sb

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

REGIONS = ["Europe", "Africa", "Latin America", "Canada", "USA"]

REGION_DETAILS = {
    "Europe":        ("SEPA/Stripe", "Contractor agreement", "GDPR-aware, LinkedIn-first, European chamber networks"),
    "Africa":        ("Flutterwave/Paystack/mobile money", "EOR or local contract", "WhatsApp-first, mobile SME outreach, NDPR/POPIA awareness"),
    "Latin America": ("PIX/SPEI/Wise", "EOR or contractor", "WhatsApp Business, referrals, LatAm entrepreneur communities"),
    "Canada":        ("Stripe/Interac", "1099-equivalent contractor", "CASL compliance, bilingual French/English, Canadian chambers"),
    "USA":           ("Stripe/ACH", "1099 independent contractor", "CAN-SPAM/TCPA awareness, LinkedIn + cold outreach, U.S. chamber networks"),
}

EEO_DEFAULT = (
    "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
    "race, colour, religion, sex, national origin, age, disability, or any other protected "
    "characteristic. All hiring decisions are based solely on qualifications, merit, and business need."
)


def _clean_json(raw: str) -> str:
    """Strip markdown fences and leading/trailing whitespace."""
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    return raw.strip()


def build_job_description(region: str, eeo: str = EEO_DEFAULT) -> dict:
    """
    Two-call approach:
    Call 1 — structured JSON (lists only, no long prose fields).
    Call 2 — full plain-text JD assembled from structured data.
    Avoids JSON parse errors caused by multi-line prose inside JSON strings.
    """
    pay_method, contract_type, region_ctx = REGION_DETAILS.get(
        region, ("Stripe", "Contractor", "")
    )

    # ── Call 1: structured fields only ──────────────────────────────
    structured_prompt = f"""Generate structured content for a SmartSMBAI Certified Growth Agent job posting for the {region} market.

ROLE: Certified Growth Agent — commission-only partnership (no base salary)
PLATFORM: SmartSMBAI — productized AI systems (receptionists, lead agents, support assistants) for SMBs
COMMISSION: 15% build fee + 10% monthly (months 1-12 per client) + 5% territory override
PAYMENT: {pay_method}
CONTRACTING: {contract_type}
REGION: {region_ctx}

REQUIREMENTS:
- 2+ years B2B sales, SaaS affiliate, agency, or consulting
- Named SME chamber, trade org, or entrepreneur network in {region}
- AI tool comfort — can explain value to non-technical SMB owners
- Commission-only comfort and pipeline management ability
- Completes 4-hour SmartSMBAI certification before onboarding clients

Return ONLY valid JSON with SHORT string values — NO multi-line strings, NO embedded newlines:
{{
  "role_title": "Certified Growth Agent — {region}",
  "region": "{region}",
  "role_summary": "One sentence: compelling overview of the opportunity.",
  "what_youll_do": [
    "Prospect and close SMB owners in {region} on AI-powered business tools",
    "Run product demos and handle objections for a commission-based sale",
    "Onboard clients and monitor AI assistant performance post-launch",
    "Build and grow a referral network within local SME chambers",
    "Report pipeline activity and client adoption metrics weekly"
  ],
  "what_we_need": [
    "2+ years B2B sales, agency, SaaS affiliate, or business consulting",
    "Active membership in a named SME chamber or entrepreneur network in {region}",
    "Comfortable using and explaining AI tools to non-technical buyers",
    "Ability to diagnose basic AI output quality issues",
    "Commission-only comfort with strong pipeline discipline"
  ],
  "nice_to_have": [
    "Experience selling SaaS or tech products to SMBs",
    "Existing warm relationships with business owners in {region}",
    "Familiarity with CRM tools and outreach automation"
  ],
  "compensation": [
    "15% commission on each client build fee (one-time)",
    "10% monthly residual on subscription for first 12 months per client",
    "5% territory override on closings by any sub-partners you refer",
    "Payment via {pay_method} — no cap on earnings",
    "Average active partner earns $2,000-$5,000/month within 6 months"
  ],
  "social_teaser_short": "Under 280 chars teaser for X/Twitter about this role.",
  "social_teaser_linkedin": "3 sentences for a LinkedIn post about this opportunity.",
  "keywords": ["B2B sales", "commission", "AI", "SaaS", "SMB", "{region}", "Growth Agent", "remote"]
}}

RULES:
- Every value must be a short string or array of short strings
- NO newlines inside any string value
- NO apostrophes that could break JSON — use the word instead (e.g. "do not" not "don't")
- Return ONLY the JSON object, nothing else"""

    try:
        resp1 = client.messages.create(
            model=MODEL, max_tokens=1500,
            messages=[{"role": "user", "content": structured_prompt}]
        )
        raw1  = _clean_json(resp1.content[0].text)
        data  = json.loads(raw1)
    except Exception as e:
        return {"error": f"Structured generation failed: {e}"}

    # ── Call 2: full plain-text JD ───────────────────────────────────
    prose_prompt = f"""Write a complete plain-text job posting for SmartSMBAI.
Use the content below. Write as flowing plain text — no JSON, no code, no markdown fences.

ROLE: {data.get('role_title', f'Certified Growth Agent — {region}')}
REGION: {region}
REGION CONTEXT: {region_ctx}

WHAT YOULL DO:
{chr(10).join('- ' + r for r in data.get('what_youll_do', []))}

WHAT WE NEED:
{chr(10).join('- ' + r for r in data.get('what_we_need', []))}

NICE TO HAVE:
{chr(10).join('- ' + r for r in data.get('nice_to_have', []))}

COMPENSATION:
{chr(10).join('- ' + r for r in data.get('compensation', []))}

HOW TO APPLY: Send your background and the local business network you would bring to info@smartsmbai.com
Subject line: Application — Growth Agent — {region} — [Your Name]

EEO: {eeo}

Write a complete job posting with these sections in order:
ABOUT SMARTSMBAI / THE OPPORTUNITY / WHAT YOU WILL DO / WHAT WE ARE LOOKING FOR / COMPENSATION / GOOD TO KNOW / HOW TO APPLY

Output only the job posting text. No preamble."""

    try:
        resp2 = client.messages.create(
            model=MODEL, max_tokens=1500,
            messages=[{"role": "user", "content": prose_prompt}]
        )
        full_jd = resp2.content[0].text.strip()
    except Exception as e:
        # Fall back to assembling from structured data
        full_jd = _assemble_jd(data, region, eeo)

    data["full_jd"]        = full_jd
    data["eeo_statement"]  = eeo
    data["pay_method"]     = pay_method
    data["contract_type"]  = contract_type
    return data


def _assemble_jd(data: dict, region: str, eeo: str) -> str:
    """Fallback: assemble plain-text JD from structured fields."""
    lines = [
        f"CERTIFIED GROWTH AGENT — {region.upper()}",
        f"SmartSMBAI | Commission Partnership | {region}",
        "",
        "ABOUT SMARTSMBAI",
        "SmartSMBAI delivers productized AI systems — receptionists, lead agents, and support assistants — for small and medium businesses. We are expanding our Growth Agent network across {region}.".format(region=region),
        "",
        "THE OPPORTUNITY",
        data.get("role_summary", ""),
        "",
        "WHAT YOU WILL DO",
    ]
    for r in data.get("what_youll_do", []):
        lines.append(f"- {r}")
    lines += ["", "WHAT WE ARE LOOKING FOR"]
    for r in data.get("what_we_need", []):
        lines.append(f"- {r}")
    if data.get("nice_to_have"):
        lines += ["", "NICE TO HAVE"]
        for r in data["nice_to_have"]:
            lines.append(f"- {r}")
    lines += ["", "COMPENSATION"]
    for r in data.get("compensation", []):
        lines.append(f"- {r}")
    lines += [
        "",
        "HOW TO APPLY",
        "Send your background and the local business network you would bring to info@smartsmbai.com",
        f"Subject line: Application — Growth Agent — {region} — [Your Name]",
        "",
        eeo,
    ]
    return "\n".join(lines)


def save_job_description(jd_data: dict) -> str:
    """Save generated JD to Supabase. Returns new row id."""
    if not _sb:
        return ""
    try:
        row = {
            "role_title":       jd_data.get("role_title", ""),
            "role_level":       "Commission Partner",
            "department":       "Sales",
            "location":         jd_data.get("region", jd_data.get("location", "")),
            "employment_type":  jd_data.get("contract_type", "Contractor"),
            "salary_range":     "Commission-only (15% build + 10% monthly + 5% override)",
            "full_jd":          jd_data.get("full_jd", ""),
            "summary":          jd_data.get("role_summary", ""),
            "key_requirements": jd_data.get("what_we_need", []),
            "nice_to_haves":    jd_data.get("nice_to_have", []),
            "social_teaser":    jd_data.get("social_teaser_linkedin", ""),
            "status":           "draft",
        }
        res = _sb.table("job_descriptions").insert(row).execute()
        return res.data[0]["id"] if res.data else ""
    except Exception as e:
        print(f"[JDAgent] save error: {e}")
        return ""


def get_job_descriptions(status: str = None) -> list:
    """Fetch all saved JDs from Supabase, newest first."""
    if not _sb:
        return []
    try:
        q = _sb.table("job_descriptions").select("*").order("created_at", desc=True)
        if status:
            q = q.eq("status", status)
        return q.execute().data or []
    except Exception as e:
        print(f"[JDAgent] get error: {e}")
        return []
