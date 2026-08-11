"""
cv_agent.py — Agent 2: CV Screening (SmartSMBAI)
Single role: Certified Growth Agent. Variation is by REGION, not role.
7 SmartSMBAI-specific dimensions. AI gate enforced (≥3 on AI dims).
Commission model check embedded in prompt. Compliance note mandatory.
System prompt embedded — no external .txt file dependency.
"""
import os, json
from dotenv import load_dotenv
import anthropic
from database import save_cv_score, update_candidate_status, _sb

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL  = "claude-sonnet-4-6"

ADVANCE_THRESHOLD = 22   # out of 35
MIN_ANY_DIM       = 2
MIN_AI_DIM        = 3    # tech_ai, ai_troubleshoot, ai_adoption must all be ≥ 3

AI_DIMS = {
    "tech_ai_prompting_readiness",
    "ai_troubleshooting_integration_privacy",
    "ai_adoption_metrics_thinking",
}

DIM_KEYS = [
    "sales_track_record",
    "local_network_proof",
    "tech_ai_prompting_readiness",
    "ai_troubleshooting_integration_privacy",
    "ai_adoption_metrics_thinking",
    "communication_clarity",
    "region_fit",
]

REGION_CONTEXT = {
    "Africa":        "WhatsApp-first outreach, mobile money comfort, local SME chamber networks, NDPR/POPIA awareness, named African market knowledge.",
    "Latin America": "WhatsApp and Spanish/Portuguese fluency, LatAm SME networks, informal B2B relationship-building ability.",
    "Europe":        "LinkedIn-first outreach, GDPR compliance awareness, SEPA payments, formal B2B networking, named European market.",
    "Canada":        "French-English bilingualism (Quebec advantage), CASL email compliance, Canadian SME landscape, professional LinkedIn presence.",
    "USA":           "1099 independent contractor comfort, LinkedIn + cold outreach, CAN-SPAM/TCPA awareness, USA SME market knowledge.",
}

SYSTEM_PROMPT = """You are the SmartSMBAI CV Screening Agent (Agent 2).
Your job is to screen Certified Growth Agent applicants using job-relevant evidence only.

RULES:
- Score only on explicit, verifiable evidence in the CV and cover letter
- Never infer, assume, or guess qualifications not stated
- Never consider age, gender, ethnicity, nationality, religion, disability, or family status
- Return only valid JSON — no preamble, no explanation
- Flag AI gate risk clearly when AI dimensions score below 3"""


def screen_cv(application_id: str, candidate_name: str, region: str,
              cv_text: str, cover_letter: str) -> dict:
    """Score one candidate's CV against the SmartSMBAI 7-dimension rubric."""
    region_ctx = REGION_CONTEXT.get(region, "General Growth Agent market.")

    prompt = f"""Screen this Certified Growth Agent application for SmartSMBAI.

CANDIDATE: {candidate_name}
REGION: {region}
REGION CONTEXT: {region_ctx}
ADVANCE THRESHOLD: {ADVANCE_THRESHOLD}/35 total, no dimension below {MIN_ANY_DIM},
                   all three AI dimensions must be ≥ {MIN_AI_DIM}

COVER LETTER:
{cover_letter[:2000] or "(none provided)"}

CV / RESUME:
{cv_text[:4000] or "(none provided)"}

Score this candidate 1 (very weak) to 5 (strong) on each dimension:

1. sales_track_record
   Evidence of B2B sales results: deal sizes, pipeline volumes, closure rates, named clients.
   1 = no sales evidence | 5 = specific, quantified, credible B2B sales track record

2. local_network_proof
   Named chambers, trade orgs, entrepreneur communities, WhatsApp groups in {region}.
   1 = generic "I have a network" | 5 = specific, named, verifiable networks

3. tech_ai_prompting_readiness  ← AI GATE DIMENSION (must score ≥ {MIN_AI_DIM})
   Comfort with AI tools, ability to prompt effectively, CRM fluency, demo-ready.
   1 = no tech evidence | 5 = specific AI tools named with concrete use cases

4. ai_troubleshooting_integration_privacy  ← AI GATE DIMENSION (must score ≥ {MIN_AI_DIM})
   Can diagnose AI output issues, understands integrations, data privacy judgment.
   1 = no understanding | 5 = clear troubleshooting ability evidenced in CV

5. ai_adoption_metrics_thinking  ← AI GATE DIMENSION (must score ≥ {MIN_AI_DIM})
   Post-implementation thinking: adoption barriers, accuracy, metrics tracking.
   1 = no metrics awareness | 5 = specific KPIs and success frameworks mentioned

6. communication_clarity
   Writing quality, structure, specificity, and professionalism of application.
   1 = unclear or generic | 5 = well-structured, specific, professionally written

7. region_fit
   {region}-specific market knowledge, language fit, cultural and regulatory awareness.
   1 = no regional fit evidence | 5 = strong, specific {region} market knowledge

COMMISSION MODEL CHECK: Does the CV or cover letter acknowledge or show comfort with
commission-only or performance-based earnings? (true/false)

Return ONLY valid JSON:
{{
  "sales_track_record":                    int 1-5,
  "local_network_proof":                   int 1-5,
  "tech_ai_prompting_readiness":           int 1-5,
  "ai_troubleshooting_integration_privacy":int 1-5,
  "ai_adoption_metrics_thinking":          int 1-5,
  "communication_clarity":                 int 1-5,
  "region_fit":                            int 1-5,
  "recommendation":  "Advance" | "Hold" | "Reject",
  "commission_comfort": true or false,
  "summary": "3-5 direct sentences assessing this candidate for a {region} Growth Agent role",
  "green_flags": ["up to 5 specific positive signals from the CV"],
  "red_flags":   ["up to 5 concerns or gaps"],
  "compliance_note": "REQUIRED — one sentence confirming: This assessment used job-relevant evidence only. No protected characteristics were referenced or considered, including race, colour, religion, sex, national origin, age, disability, or genetic information."
}}

SCORING RULES:
- Advance: total ≥ {ADVANCE_THRESHOLD}, no dim < {MIN_ANY_DIM}, all AI dims ≥ {MIN_AI_DIM}
- Reject: total < {ADVANCE_THRESHOLD - 8} OR multiple dims = 1
- Hold: everything else, including AI gate failure (strong sales but AI dims < {MIN_AI_DIM})
- If AI dims score below {MIN_AI_DIM}, set recommendation to "Hold" regardless of total score"""

    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=2000, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        )
        raw  = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        scores = {k: data.get(k, 0) for k in DIM_KEYS}
        total  = sum(scores.values())
        rec    = data.get("recommendation","Hold")

        # Enforce AI gate
        ai_min = min(scores.get(d, 0) for d in AI_DIMS)
        if ai_min < MIN_AI_DIM and rec == "Advance":
            rec = "Hold"

        # Save to Supabase
        save_cv_score(
            application_id = application_id,
            scores         = scores,
            recommendation = rec,
            summary        = data.get("summary",""),
            green_flags    = data.get("green_flags",[]),
            red_flags      = data.get("red_flags",[]),
        )

        return {
            "scores":           scores,
            "total":            total,
            "recommendation":   rec,
            "summary":          data.get("summary",""),
            "green_flags":      data.get("green_flags",[]),
            "red_flags":        data.get("red_flags",[]),
            "commission_comfort": data.get("commission_comfort", False),
            "compliance_note":  data.get("compliance_note",""),
            "ai_gate_passed":   ai_min >= MIN_AI_DIM,
            "ai_gate_min":      ai_min,
        }
    except Exception as e:
        return {
            "error":          str(e),
            "recommendation": "Hold",
            "summary":        f"CV screening failed: {e}",
            "scores":         {k: 0 for k in DIM_KEYS},
            "total":          0,
            "green_flags":    [],
            "red_flags":      [f"Processing error: {e}"],
            "commission_comfort": False,
            "ai_gate_passed": False,
        }


def run_cv_screening(application_id: str, candidate_id: str, candidate_name: str,
                     region: str, cv_text: str, cover_letter: str) -> dict:
    """Entry point called from the Streamlit page."""
    return screen_cv(application_id, candidate_name, region, cv_text, cover_letter)


def batch_screen_all(region_filter: str = None) -> list:
    """
    Screen all candidates with status 'new' or 'screening'.
    Optionally filter by region. Returns list of result dicts.
    """
    if not _sb:
        return []
    results = []
    for status in ("new", "screening"):
        try:
            q = _sb.table("candidates").select("*").eq("status", status)
            if region_filter:
                q = q.eq("region", region_filter)
            cands = q.execute().data or []
        except Exception as e:
            print(f"[CVAgent] batch fetch {status}: {e}"); continue

        for cand in cands:
            cid     = cand.get("id","")
            name    = cand.get("name","?")
            region  = cand.get("region","Unknown")
            cv_text = ""
            cover   = ""
            app_id  = ""
            try:
                ar = (_sb.table("applications").select("*")
                      .eq("candidate_id", cid).limit(1).execute())
                if ar.data:
                    a       = ar.data[0]
                    cv_text = a.get("cv_text","")
                    cover   = a.get("cover_letter_text","")
                    app_id  = a.get("id","")
            except Exception as e:
                print(f"[CVAgent] app fetch for {name}: {e}")

            result = screen_cv(app_id, name, region, cv_text, cover)
            result["candidate_name"] = name
            result["candidate_id"]   = cid
            result["region"]         = region

            # Update candidate status based on recommendation
            new_status = {
                "Advance": "interview_sent",
                "Reject":  "rejected",
            }.get(result.get("recommendation","Hold"), "screening")
            try:
                update_candidate_status(cid, new_status, actor="cv_agent")
            except Exception as e:
                print(f"[CVAgent] status update for {name}: {e}")

            results.append(result)

    return results
