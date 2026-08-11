"""Pages/7_Live_Interview.py — Agent 7: Live Interview via Vapi (SmartSMBAI)"""
import streamlit as st, os, httpx, json
from dotenv import load_dotenv
from database import get_candidates, update_candidate_status, _sb

load_dotenv()

st.set_page_config(page_title="Live Interview — SmartSMBAI", page_icon="🎙️", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#059669);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#A7F3D0;margin-left:10px'>
Agent 7 — Live Interview · Vapi AI Voice · Certified Growth Agent</span>
</div>""", unsafe_allow_html=True)

VAPI_API_KEY    = os.getenv("VAPI_API_KEY", "8a0b5a88-cd75-476e-9974-0a60bd77ca8c")
VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY", "a6903c3c-f09f-404e-ae12-334843f5b156")
INTERVIEW_PAGE_URL = os.getenv("INTERVIEW_PAGE_URL", "https://smartsmbai-hr-suite.streamlit.app/Candidate_Interview")
APP_URL = os.getenv("APP_URL", "https://smartsmbai-hr-suite.streamlit.app")

REGION_FOLLOW_UPS = {
    "Europe":        "You mentioned local networks. Which specific European chambers or B2B communities would you prioritise in your first 30 days?",
    "Africa":        "How would you use WhatsApp Business to run your first 5 discovery calls with African SME owners?",
    "Latin America": "Walk me through how you'd build a referral chain from your first client in Latin America.",
    "Canada":        "How would you adapt your pitch for a Quebec market where French-language communication matters?",
    "USA":           "How would you explain the 1099 commission-only structure to a U.S. business owner who asks about salary?",
}

def create_vapi_call(candidate_name: str, candidate_phone: str, region: str) -> dict:
    region_q = REGION_FOLLOW_UPS.get(region, "What makes you the right fit for the Growth Agent role in your market?")
    payload = {
        "type": "outboundPhoneCall",
        "phoneNumberId": None,
        "customer": {"number": candidate_phone, "name": candidate_name},
        "assistant": {
            "name": "SmartSMBAI Live Interviewer",
            "voice": {"provider": "11labs", "voiceId": "rachel"},
            "model": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "systemPrompt": f"""You are conducting a structured live interview for SmartSMBAI.
You are speaking with {candidate_name}, a Certified Growth Agent candidate for the {region} market.

INTERVIEW STRUCTURE (15-20 minutes):
1. Welcome and brief intro (1 min)
2. Sales experience deep-dive — ask for specific deal sizes and timelines (3 min)
3. Local network proof — ask them to name specific organisations they'd contact this week (3 min)
4. AI readiness check — ask them to explain what a prompt is to a non-technical SMB owner (3 min)
5. Commission model comfort — ask how they'd manage 90-day pipeline without a base salary (3 min)
6. Region-specific question: {region_q} (3 min)
7. Close — ask if they have questions, confirm next steps (2 min)

RULES:
- Be warm, professional, and direct
- Push for specifics when answers are vague — "Can you give me a specific example?"
- Never discuss salary, protected characteristics, or anything outside the role
- End clearly: "Thank you {candidate_name}, we'll be in touch within 48 hours."
- Keep total call under 20 minutes""",
            },
            "firstMessage": f"Hello {candidate_name}, this is the SmartSMBAI AI interviewer. Thank you for applying for the Certified Growth Agent role. I have about 15-20 minutes with you today. Are you ready to begin?",
            "endCallMessage": f"Thank you {candidate_name}. That's all for today. We'll review your interview and be in touch within 48 hours. Have a great day!",
            "recordingEnabled": True,
            "transcriptEnabled": True,
        }
    }
    headers = {"Authorization": f"Bearer {VAPI_API_KEY}", "Content-Type": "application/json"}
    try:
        r = httpx.post("https://api.vapi.ai/call", json=payload, headers=headers, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def create_web_interview_session(candidate_id: str, candidate_name: str, region: str) -> dict:
    region_q = REGION_FOLLOW_UPS.get(region, "What makes you the right fit for the Growth Agent role?")
    if not _sb:
        return {"error": "Supabase not connected"}
    try:
        res = _sb.table("live_interview_sessions").insert({
            "candidate_id":   candidate_id,
            "candidate_name": candidate_name,
            "region":         region,
            "interview_type": "web",
            "status":         "pending",
            "region_question": region_q,
        }).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        return {"error": str(e)}

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    interview_type = st.radio("Interview Mode", ["🌐 Web (Candidate Link)", "📞 Phone (Vapi Call)"])
    st.markdown("---")
    st.caption("**Web mode** sends the candidate a link to complete a structured text interview.\n\n**Phone mode** initiates a live AI voice call via Vapi.")

# ── Load candidates ──────────────────────────────────────────────────
shortlisted = get_candidates(status="shortlisted")
if not shortlisted:
    st.info("No shortlisted candidates yet. Score candidates in Agent 5 and shortlist them first.")
    st.stop()

st.markdown(f"### {len(shortlisted)} Shortlisted Candidate(s) — Ready for Live Interview")

for c in shortlisted:
    cid    = c.get("id", "")
    name   = c.get("name", "?")
    region = c.get("region", "Unknown")
    email  = c.get("email", "")

    with st.expander(f"**{name}** — {region}", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Region", region)
        col2.metric("Email", email)
        col3.metric("Status", c.get("status","").replace("_"," ").title())

        if "🌐" in interview_type:
            st.markdown("**Send Web Interview Link**")

            # Check if session already exists
            existing = None
            if _sb:
                try:
                    r = _sb.table("live_interview_sessions").select("*").eq("candidate_id", cid).execute()
                    existing = r.data[0] if r.data else None
                except Exception:
                    pass

            if existing:
                session_id = existing.get("id","")
                interview_url = f"{INTERVIEW_PAGE_URL}?session={session_id}"
                st.success(f"✅ Interview session already created")
                st.code(interview_url)
                st.caption("Share this link with the candidate. They complete the interview in their browser.")
            else:
                if st.button(f"🌐 Create Interview Link for {name}", key=f"web_{cid}", type="primary"):
                    session = create_web_interview_session(cid, name, region)
                    if "error" in session:
                        st.error(f"Error: {session['error']}")
                    else:
                        session_id = session.get("id", "")
                        interview_url = f"{INTERVIEW_PAGE_URL}?session={session_id}"
                        update_candidate_status(cid, "live_interview_sent", actor="HR")
                        st.success("✅ Session created!")
                        st.code(interview_url)
                        st.caption("Share this link with the candidate.")
                        st.rerun()

        else:
            st.markdown("**Initiate Phone Interview (Vapi)**")
            phone = st.text_input(f"Candidate phone number (+country code)", key=f"phone_{cid}",
                                   placeholder="+447911123456")
            if st.button(f"📞 Call {name}", key=f"call_{cid}", type="primary"):
                if not phone:
                    st.warning("Enter a phone number first.")
                else:
                    with st.spinner(f"Initiating Vapi call to {name}…"):
                        result = create_vapi_call(name, phone, region)
                    if "error" in result:
                        st.error(f"Vapi error: {result['error']}")
                    else:
                        call_id = result.get("id","")
                        update_candidate_status(cid, "live_interview_sent", actor="HR")
                        if _sb:
                            try:
                                _sb.table("live_interview_sessions").insert({
                                    "candidate_id":   cid,
                                    "candidate_name": name,
                                    "region":         region,
                                    "interview_type": "phone",
                                    "status":         "in_progress",
                                    "vapi_call_id":   call_id,
                                }).execute()
                            except Exception:
                                pass
                        st.success(f"✅ Call initiated! Vapi call ID: `{call_id}`")
                        st.caption("The AI interviewer is now calling the candidate. Results will appear in Agent 8 — Live Score.")
