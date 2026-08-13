"""
jd_agent.py — Agent A backend (SmartSMBAI) v3
No JSON parsing at all. Uses section delimiters that Claude can't accidentally break.
Each section is plain text that gets parsed into lists by Python.
"""
import os, re
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
    "USA":           ("Stripe/ACH", "1099 independent contractor", "CAN-SPAM/TCPA awareness, LinkedIn outreach, U.S. chamber networks"),
}

EEO_DEFAULT = (
    "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
    "race, colour, religion, sex, national origin, age, disability, or any other protected "
    "characteristic. All hiring decisions are based solely on qualifications, merit, and business need."
)


def _parse_section(text: str, tag: str) -> list:
    """Extract lines between <TAG> and </TAG> as a cleaned list."""
    pattern = rf'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    block = match.group(1).strip()
    lines = []
    for line in block.splitlines():
        line = line.strip().lstrip('-•*').strip()
        if line:
            lines.append(line)
    return lines


def _parse_field(text: str, tag: str) -> str:
    """Extract single value between <TAG> and </TAG>."""
    pattern = rf'<{tag}>(.*?)</{tag}>'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def build_job_description(region: str, eeo: str = EEO_DEFAULT) -> dict:
    """
    Single API call using XML-style section tags.
    No JSON parsing — immune to apostrophes, quotes, and special characters.
    """
    pay_method, contract_type, region_ctx = REGION_DETAILS.get(
        region, ("Stripe", "Contractor", "")
    )

    prompt = f"""Write a SmartSMBAI Certified Growth Agent job posting for the {region} market.

ROLE: Certified Growth Agent (commission-only, no base salary)
PLATFORM: SmartSMBAI — AI receptionists, lead agents, support assistants for SMBs
COMMISSION: 15% build fee + 10% monthly (months 1-12 per client) + 5% territory override
PAYMENT: {pay_method}
CONTRACTING: {contract_type}
REGION CONTEXT: {region_ctx}

Output your response using EXACTLY these XML section tags. Write real content inside each tag.

<role_summary>
One compelling sentence describing this opportunity for a {region} Growth Agent.
</role_summary>

<what_youll_do>
- First responsibility
- Second responsibility
- Third responsibility
- Fourth responsibility
- Fifth responsibility
- Sixth responsibility
</what_youll_do>

<what_we_need>
- First requirement
- Second requirement
- Third requirement
- Fourth requirement
- Fifth requirement
</what_we_need>

<nice_to_have>
- First nice-to-have
- Second nice-to-have
- Third nice-to-have
</nice_to_have>

<compensation>
- 15 percent commission on each client build fee paid as a one-time amount
- 10 percent monthly residual on subscription for first 12 months per client
- 5 percent territory override on closings by any sub-partners you refer
- Payment via {pay_method} with no cap on earnings
- Average active partner earns between 2000 and 5000 USD per month within 6 months
</compensation>

<social_short>
Under 280 character teaser for Twitter about this Growth Agent role in {region}.
</social_short>

<social_linkedin>
Three sentence LinkedIn post about this Growth Agent opportunity in {region}.
</social_linkedin>

<full_jd>
CERTIFIED GROWTH AGENT — {region.upper()}
SmartSMBAI | Commission Partnership | {region}

ABOUT SMARTSMBAI
[2-3 sentences about SmartSMBAI and what Growth Agents do]

THE OPPORTUNITY
[2-3 sentences about this specific {region} opportunity]

WHAT YOU WILL DO
[6 bullet points]

WHAT WE ARE LOOKING FOR
[5 bullet points of requirements]

NICE TO HAVE
[3 bullet points]

COMPENSATION
[5 bullet points with specific commission details]

GOOD TO KNOW
[2-3 sentences about the commission-only structure, certification, and contractor status]

HOW TO APPLY
Send your background and the local business network you would bring to info@smartsmbai.com
Subject line: Application - Growth Agent - {region} - [Your Name]

{eeo}
</full_jd>

Write real content for every section. Do not repeat the placeholder text above.
Output only the XML tags and their content — nothing else."""

    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.content[0].text

        data = {
            "role_title":           f"Certified Growth Agent — {region}",
            "region":               region,
            "role_summary":         _parse_field(text, "role_summary"),
            "what_youll_do":        _parse_section(text, "what_youll_do"),
            "what_we_need":         _parse_section(text, "what_we_need"),
            "nice_to_have":         _parse_section(text, "nice_to_have"),
            "compensation":         _parse_section(text, "compensation"),
            "social_teaser_short":  _parse_field(text, "social_short"),
            "social_teaser_linkedin": _parse_field(text, "social_linkedin"),
            "full_jd":              _parse_field(text, "full_jd"),
            "eeo_statement":        eeo,
            "pay_method":           pay_method,
            "contract_type":        contract_type,
            "keywords": [
                "B2B sales", "commission", "AI", "SaaS", "SMB",
                region, "Growth Agent", "remote", "affiliate"
            ],
        }

        # Fallback: if full_jd is empty, assemble from sections
        if not data["full_jd"].strip():
            data["full_jd"] = _assemble_jd(data, region, eeo)

        return data

    except Exception as e:
        return {"error": str(e)}


def _assemble_jd(data: dict, region: str, eeo: str) -> str:
    """Fallback: build plain-text JD from parsed sections."""
    lines = [
        f"CERTIFIED GROWTH AGENT — {region.upper()}",
        f"SmartSMBAI | Commission Partnership | {region}",
        "",
        "ABOUT SMARTSMBAI",
        "SmartSMBAI delivers productized AI systems — receptionists, lead agents, and support assistants — for small and medium businesses. We are expanding our Growth Agent network.",
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
        f"Subject line: Application - Growth Agent - {region} - [Your Name]",
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
