"""
jd_agent.py — Agent A backend (SmartSMBAI)
Generates Certified Growth Agent job descriptions per region.
Saves to Supabase job_descriptions table. Provides get_job_descriptions()
for Agent B to load from library.
"""
import os, json
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
    "Canada":        ("Stripe/Interac", "1099-equivalent contractor", "CASL compliance, bilingual (French/English), Canadian chambers"),
    "USA":           ("Stripe/ACH", "1099 independent contractor", "CAN-SPAM/TCPA awareness, LinkedIn + cold outreach, U.S. chamber networks"),
}

EEO_DEFAULT = (
    "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
    "race, colour, religion, sex, national origin, age, disability, or any other protected "
    "characteristic. All hiring decisions are based solely on qualifications, merit, and business need."
)

SYSTEM_PROMPT = """You are SmartSMBAI's Job Description Writer.
You write compelling, accurate, region-specific job postings for the Certified Growth Agent role.
Return only valid JSON — no preamble, no explanation, no markdown fences."""


def build_job_description(region: str, eeo: str = EEO_DEFAULT) -> dict:
    pay_method, contract_type, region_ctx = REGION_DETAILS.get(region, ("Stripe", "Contractor", ""))

    prompt = f"""Write a publish-ready job posting for SmartSMBAI's Certified Growth Agent role in the {region} market.

ROLE: Certified Growth Agent (commission-only partnership — no base salary)
PLATFORM: SmartSMBAI — productized AI systems (receptionists, lead agents, support assistants) for SMBs
COMMISSION: 15% of one-time build fee + 10% monthly subscription (months 1-12 per client) + 5% territory override on sub-partner closings
PAYMENT: {pay_method}
CONTRACTING: {contract_type}
REGION CONTEXT: {region_ctx}

REQUIREMENTS:
- 2+ years B2B sales, SaaS affiliate, marketing agency, or business consulting
- Active named SME chamber, trade organisation, or entrepreneur network in {region}
- Comfortable using and explaining AI tools to non-technical buyers
- Can diagnose basic AI output issues — accuracy, hallucinations, privacy
- Commission-only comfort — pipeline management without a base salary
- Completes 4-hour SmartSMBAI certification before onboarding clients

EEO STATEMENT: {eeo}

Return ONLY valid JSON:
{{
  "role_title": "Certified Growth Agent — {region}",
  "region": "{region}",
  "role_summary": "3 compelling sentences about the opportunity",
  "what_youll_do": ["8-10 bullet strings starting with active verbs"],
  "what_we_need": ["6-8 required qualifications as bullet strings"],
  "nice_to_have": ["3-5 optional qualifications"],
  "compensation": ["4-5 bullet strings explaining the commission structure clearly"],
  "full_jd": "complete plain-text job description with all sections — role overview, responsibilities, requirements, compensation, good to know, how to apply",
  "social_teaser_short": "under 280 chars for X/Twitter",
  "social_teaser_linkedin": "3-4 sentences for a LinkedIn post",
  "keywords": ["8-12 ATS keywords for this role and region"],
  "eeo_statement": "{eeo}"
}}"""

    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=2500, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        raw  = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        data["region"] = region
        data["pay_method"]     = pay_method
        data["contract_type"]  = contract_type
        return data
    except Exception as e:
        return {"error": str(e), "role_title": f"Certified Growth Agent — {region}", "region": region}


def save_job_description(jd_data: dict) -> str:
    """Save generated JD to Supabase. Returns new row id."""
    if not _sb:
        return ""
    try:
        row = {
            "role_title":      jd_data.get("role_title", ""),
            "role_level":      "Commission Partner",
            "department":      "Sales",
            "location":        jd_data.get("region", ""),
            "employment_type": jd_data.get("contract_type", "Contractor"),
            "salary_range":    "Commission-only (15% build + 10% monthly + 5% override)",
            "full_jd":         jd_data.get("full_jd", ""),
            "summary":         jd_data.get("role_summary", ""),
            "key_requirements": jd_data.get("what_we_need", []),
            "nice_to_haves":   jd_data.get("nice_to_have", []),
            "social_teaser":   jd_data.get("social_teaser_linkedin", ""),
            "status":          "draft",
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
