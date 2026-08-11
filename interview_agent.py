"""
interview_agent.py — Agent 3: Interview Agent (SmartSMBAI v2)
Duplicate prevention: get_existing_session, invitation_already_sent, mark_invite_sent.
12 standard + 1 region-specific questions from the SmartSMBAI playbook.
"""
import os, json
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic
from database import create_interview_session, update_session_responses, update_candidate_status, _sb, _log

load_dotenv()
client=anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL="claude-sonnet-4-6"
SYSTEM_PROMPT=open("system_prompt_interview.txt").read()

STANDARD_QUESTIONS=[
    "Walk me through your most relevant B2B sales, consulting, agency, SaaS, affiliate, or business-development experience. What did you sell or promote, who were the buyers, and what results did you produce?",
    "Describe the small-business, chamber, trade, entrepreneur, industry, or local business communities you are currently connected to. How would you introduce SmartSMBAI into those networks?",
    "Tell me about a time you explained a technical, SaaS, automation, AI, or digital product to a non-technical buyer. What was difficult for them to understand, and how did you make it clear?",
    "Which AI tools have you used in a business or sales context, such as ChatGPT, Copilot, Claude, Gemini, Zapier AI, chatbot builders, or CRM AI features? For each tool, briefly describe what you used it for and how comfortable you are explaining it to a non-technical client.",
    "Describe a time you used an AI tool, chatbot, automation platform, or prompt-based workflow to solve a business problem. What prompt or instruction did you use, what output did you receive, and how did you decide whether the result was useful?",
    "Imagine a client's AI assistant is producing inaccurate, generic, or incomplete responses after launch. What steps would you take to diagnose whether the issue is the prompt, missing knowledge-base content, poor intake materials, configuration settings, or a technical problem?",
    "Describe any experience connecting or integrating AI tools with business systems such as CRMs, calendars, email platforms, websites, forms, chat widgets, Zapier, Make, APIs, or automation workflows.",
    "What is your understanding of AI data privacy when working with client information? Describe how you would handle sensitive business data, customer details, uploaded documents, prompts, and AI outputs responsibly.",
    "After an AI assistant goes live, what adoption challenges and performance metrics would you monitor — such as response accuracy, lead capture, bookings, escalation rate, customer satisfaction, or usage trends? How would you use those insights to explain value and recommend improvements?",
    "This is a commission-based partnership with no base salary. How would you manage your outreach, pipeline activity, and cash flow during the first 90 days before commissions build up?",
    "What would make a small-business owner hesitate or say no to an AI receptionist, lead agent, or support assistant — and how would you respond to that objection?",
    "What questions do you have about SmartSMBAI, the Growth Agent role, the commission model, onboarding responsibilities, certification, or support expectations?",
]

REGION_QUESTION={
    "Europe":        "How would you approach selling SmartSMBAI in European SME markets where buyers may expect local-language support, privacy awareness, and careful contracting?",
    "Africa":        "How comfortable are you running a sales process through WhatsApp Business, local business communities, referrals, and mobile-first communication?",
    "Latin America": "How would you use WhatsApp Business, referrals, and local entrepreneur communities to build trust with small-business owners in your market?",
    "Canada":        "How would you adapt your approach for Canadian SMEs, including markets where bilingual or French-language communication may matter?",
    "USA":           "How would you build pipeline through U.S. chambers of commerce, local business associations, niche industry groups, or entrepreneur communities, and how would you explain a commission-based 1099 partnership clearly?",
    "Unknown":       "Which local business networks, chambers of commerce, or SME communities would you target first, and how would you introduce SmartSMBAI into them?",
}

def generate_questions_for_region(region: str) -> list:
    return STANDARD_QUESTIONS + [REGION_QUESTION.get(region, REGION_QUESTION["Unknown"])]

# ── Duplicate prevention ────────────────────────────────────────────
def get_existing_session(candidate_id: str) -> dict | None:
    if not _sb: return None
    try:
        res=(_sb.table("interview_sessions").select("*")
             .eq("candidate_id",candidate_id).order("created_at",desc=True).limit(1).execute())
        return res.data[0] if res.data else None
    except Exception as e: print(f"[Interview] get_existing_session: {e}"); return None

def get_sessions_for_candidates(candidate_ids: list) -> dict:
    if not _sb or not candidate_ids: return {}
    try:
        res=(_sb.table("interview_sessions").select("*")
             .in_("candidate_id",candidate_ids).order("created_at",desc=True).execute())
        result={}
        for row in (res.data or []):
            cid=row.get("candidate_id","")
            if cid and cid not in result: result[cid]=row
        return result
    except Exception as e: print(f"[Interview] get_sessions_for_candidates: {e}"); return {}

def invitation_already_sent(candidate_id: str) -> bool:
    session=get_existing_session(candidate_id)
    if not session: return False
    return bool(session.get("invite_sent_at"))

def mark_invite_sent(session_id: str) -> None:
    if not _sb: return
    try:
        _sb.table("interview_sessions").update({
            "invite_sent_at":datetime.now(timezone.utc).isoformat(),"status":"sent"
        }).eq("id",session_id).execute()
        _log("invite_sent",object_type="session",object_id=session_id,
             summary="Interview invitation email dispatched")
    except Exception as e: print(f"[Interview] mark_invite_sent: {e}")

def run_interview_setup(candidate_id: str, region: str, deadline_str: str) -> dict:
    existing=get_existing_session(candidate_id)
    if existing:
        return {"session":existing,"questions":existing.get("questions",generate_questions_for_region(region)),"already_existed":True}
    questions=generate_questions_for_region(region)
    session=create_interview_session(candidate_id,region,questions,deadline_str)
    return {"session":session,"questions":questions,"already_existed":False}

def parse_interview_responses(raw_reply: str, questions: list) -> list:
    prompt=f"""The candidate has replied to their SmartSMBAI Growth Agent interview questions.
Parse their reply and match each answer to the correct question.

QUESTIONS ASKED:
{json.dumps(questions,indent=2)}

CANDIDATE'S REPLY:
{raw_reply[:6000]}

Return ONLY valid JSON as a list:
[{{"question_id":"Q1","question":"...","answer":"..."}}]

If a question was not answered, set answer to "(no answer provided)".
Do not fabricate answers."""
    try:
        resp=client.messages.create(model=MODEL,max_tokens=3000,system=SYSTEM_PROMPT,
            messages=[{"role":"user","content":[{"type":"text","text":prompt}]}])
        raw=resp.content[0].text.strip().replace("```json","").replace("```","")
        return json.loads(raw)
    except Exception as e:
        return [{"question_id":f"Q{i+1}","question":q,"answer":"(parse error)"} for i,q in enumerate(questions)]

def submit_candidate_responses(session_id: str, candidate_id: str, raw_reply: str, questions: list) -> list:
    responses=parse_interview_responses(raw_reply, questions)
    update_session_responses(session_id, responses, status="completed")
    update_candidate_status(candidate_id, "interview_complete")
    return responses
