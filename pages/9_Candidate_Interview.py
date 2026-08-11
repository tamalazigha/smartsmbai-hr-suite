"""Pages/9_Candidate_Interview.py — Candidate-facing interview page (SmartSMBAI)"""
import streamlit as st, os
from dotenv import load_dotenv
from database import _sb

load_dotenv()

st.set_page_config(page_title="SmartSMBAI — Growth Agent Interview", page_icon="🤝", layout="centered")

# Candidate-facing branding
st.markdown("""<div style='padding:16px 20px;background:linear-gradient(135deg,#1A2B5E,#059669);
border-radius:8px;margin-bottom:24px;text-align:center'>
<div style='font-size:28px;font-weight:700;color:#fff'>Smart<span style='color:#93C5FD'>SMB</span>AI</div>
<div style='font-size:14px;color:#A7F3D0;margin-top:4px'>Certified Growth Agent — Live Interview</div>
</div>""", unsafe_allow_html=True)

# Get session ID from URL params
params = st.query_params
session_id = params.get("session", "")

if not session_id:
    st.error("No interview session found. Please use the link provided by the SmartSMBAI recruitment team.")
    st.stop()

# Load session
session = None
if _sb:
    try:
        r = _sb.table("live_interview_sessions").select("*").eq("id", session_id).limit(1).execute()
        session = r.data[0] if r.data else None
    except Exception as e:
        st.error(f"Could not load session: {e}")
        st.stop()

if not session:
    st.error("Interview session not found. Please contact info@smartsmbai.com")
    st.stop()

candidate_name = session.get("candidate_name","Candidate")
region         = session.get("region","")
region_q       = session.get("region_question","")
status         = session.get("status","pending")

if status == "completed":
    st.success(f"✅ Thank you {candidate_name} — your interview responses have been submitted successfully.")
    st.info("The SmartSMBAI team will review your responses and be in touch within 48 hours.")
    st.stop()

st.markdown(f"## Welcome, {candidate_name}")
st.markdown(f"**Region:** {region} | **Role:** Certified Growth Agent")
st.markdown("---")
st.info(
    "Please answer each question below as thoroughly as possible. "
    "There are no trick questions — we want to understand your real experience and mindset. "
    "Take your time. You can review your answers before submitting."
)

STANDARD_QUESTIONS = [
    "Walk me through your most relevant B2B sales, consulting, agency, SaaS, affiliate, or business-development experience. Be specific about results.",
    "Describe the SME chambers, trade associations, entrepreneur or local business communities you are currently connected to. Name specific ones.",
    "Tell me about a time you explained a technical, SaaS, automation, AI, or digital product to a non-technical buyer. What was the product and how did you explain it?",
    "Which AI tools have you used in a business or sales context? For each tool, describe the use case and your comfort level explaining it to a client.",
    "Describe a time you used an AI tool or prompt-based workflow to solve a business problem. What was the prompt or workflow and what was the outcome?",
    "Imagine a client's AI assistant produces inaccurate responses after launch. Walk through your step-by-step diagnostic process.",
    "Describe any experience connecting AI tools with CRMs, calendars, email, websites, Zapier, or other automation platforms.",
    "What is your understanding of AI data privacy when working with client business information? What precautions would you take?",
    "After an AI assistant goes live with a client, what adoption challenges would you anticipate and what performance metrics would you track?",
    "This is a commission-only partnership with no base salary. How would you manage your pipeline and cash flow in the first 90 days?",
    "What would make a small-business owner say no to an AI receptionist or lead agent, and how would you handle that objection?",
    "What questions do you have about SmartSMBAI, the Growth Agent role, commission model, or certification programme?",
]

if region_q:
    STANDARD_QUESTIONS.append(region_q)

# ── Interview form ────────────────────────────────────────────────────
with st.form("interview_form"):
    answers = {}
    for i, question in enumerate(STANDARD_QUESTIONS, 1):
        st.markdown(f"**Question {i} of {len(STANDARD_QUESTIONS)}**")
        st.markdown(question)
        answers[f"q{i}"] = st.text_area(
            f"Your answer to Q{i}:",
            height=120,
            key=f"ans_{i}",
            placeholder="Type your answer here…",
            label_visibility="collapsed",
        )
        st.markdown("---")

    submitted = st.form_submit_button("✅ Submit My Interview Responses", type="primary", use_container_width=True)

if submitted:
    # Validate all answered
    empty = [i+1 for i, (k,v) in enumerate(answers.items()) if not v.strip()]
    if empty:
        st.error(f"Please answer all questions. Missing: Q{', Q'.join(map(str,empty))}")
    else:
        # Save responses
        responses = [
            {"question_id": f"Q{i}", "question": q, "answer": answers[f"q{i}"]}
            for i, q in enumerate(STANDARD_QUESTIONS, 1)
        ]
        transcript = "\n\n".join([
            f"Q{i}: {q}\nANSWER: {answers[f'q{i}']}"
            for i, q in enumerate(STANDARD_QUESTIONS, 1)
        ])

        if _sb:
            try:
                _sb.table("live_interview_sessions").update({
                    "status":    "completed",
                    "responses": responses,
                    "transcript": transcript,
                }).eq("id", session_id).execute()

                # Update candidate status
                candidate_id = session.get("candidate_id","")
                if candidate_id:
                    _sb.table("candidates").update(
                        {"status": "live_interview_complete"}
                    ).eq("id", candidate_id).execute()
            except Exception as e:
                st.error(f"Submission error: {e}")
                st.stop()

        st.success(f"✅ Thank you {candidate_name}! Your responses have been submitted.")
        st.info("We'll review your interview and be in touch within 48 hours at the email you applied from.")
        st.balloons()
        st.rerun()
