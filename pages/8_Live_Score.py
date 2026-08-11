"""Pages/8_Live_Score.py — Agent 8: Live Interview Scoring (SmartSMBAI)"""
import streamlit as st, os, json, anthropic
from dotenv import load_dotenv
from database import get_candidates, update_candidate_status, _sb

load_dotenv()

st.set_page_config(page_title="Live Score — SmartSMBAI", page_icon="📊", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#D97706);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#FEF3C7;margin-left:10px'>
Agent 8 — Live Score · Post-Live Interview Scoring · SmartSMBAI Rubric</span>
</div>""", unsafe_allow_html=True)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DIM_LABELS = {
    "sales_track_record":                    "Sales",
    "local_network_proof":                   "Network",
    "tech_ai_prompting_readiness":           "Tech/AI",
    "ai_troubleshooting_integration_privacy":"Troubleshoot",
    "ai_adoption_metrics_thinking":          "Adoption",
    "communication_clarity":                 "Comms",
    "region_fit":                            "Region Fit",
}
AI_DIMS = {"tech_ai_prompting_readiness","ai_troubleshooting_integration_privacy","ai_adoption_metrics_thinking"}
MIN_AI_DIM = 3

def score_live_interview(session_id: str, candidate_name: str, region: str, transcript: str) -> dict:
    prompt = f"""Score this SmartSMBAI live interview transcript.

CANDIDATE: {candidate_name}
REGION: {region}
ADVANCE THRESHOLD: 22/35 total, no dim < 2, all AI dims ≥ {MIN_AI_DIM}

LIVE INTERVIEW TRANSCRIPT:
{transcript[:5000]}

Score each dimension 1 (weak) to 5 (strong):
1. sales_track_record — Specific quantified B2B results, named clients, timelines
2. local_network_proof — Named {region} organisations, communities, warm contacts
3. tech_ai_prompting_readiness — AI tool fluency, prompting comfort, demo ability  ← AI GATE
4. ai_troubleshooting_integration_privacy — Diagnose issues, integration sense, privacy awareness  ← AI GATE
5. ai_adoption_metrics_thinking — Adoption barriers, post-launch metrics  ← AI GATE
6. communication_clarity — Spoken clarity, structure, directness in live setting
7. region_fit — {region}-specific market knowledge, channel comfort, cultural fit

Return ONLY valid JSON:
{{
  "sales_track_record": int 1-5,
  "local_network_proof": int 1-5,
  "tech_ai_prompting_readiness": int 1-5,
  "ai_troubleshooting_integration_privacy": int 1-5,
  "ai_adoption_metrics_thinking": int 1-5,
  "communication_clarity": int 1-5,
  "region_fit": int 1-5,
  "recommendation": "Advance to Offer" | "Hold" | "Reject",
  "commission_comfort_confirmed": true or false,
  "summary": "4-6 sentences assessing the live interview performance",
  "evidence_highlights": ["up to 5 specific strong moments"],
  "risks": ["up to 5 concerns from the live interview"],
  "compliance_note": "Confirm no protected characteristics were used in scoring"
}}"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw  = resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        scores = {k: data.get(k, 1) for k in DIM_LABELS}
        total  = sum(scores.values())
        rec    = data.get("recommendation", "Hold")
        ai_min = min(scores.get(d, 0) for d in AI_DIMS)
        if ai_min < MIN_AI_DIM and rec == "Advance to Offer":
            rec = "Hold"

        if _sb and session_id:
            try:
                _sb.table("live_interview_scores").insert({
                    "session_id":                 session_id,
                    "scores":                     scores,
                    "total_score":                total,
                    "recommendation":             rec,
                    "summary":                    data.get("summary",""),
                    "evidence_highlights":        data.get("evidence_highlights",[]),
                    "risks":                      data.get("risks",[]),
                    "compliance_note":            data.get("compliance_note",""),
                    "commission_comfort_confirmed":data.get("commission_comfort_confirmed", False),
                }).execute()
            except Exception as e:
                st.warning(f"DB save warning: {e}")

        return {
            "scores": scores, "total": total, "recommendation": rec,
            "summary": data.get("summary",""),
            "evidence_highlights": data.get("evidence_highlights",[]),
            "risks": data.get("risks",[]),
            "compliance_note": data.get("compliance_note",""),
            "commission_comfort_confirmed": data.get("commission_comfort_confirmed", False),
            "ai_gate_passed": ai_min >= MIN_AI_DIM,
            "ai_gate_min": ai_min,
        }
    except Exception as e:
        return {"error": str(e), "recommendation": "Hold", "scores": {}, "total": 0,
                "evidence_highlights": [], "risks": [], "ai_gate_passed": False}

# ── Load candidates ──────────────────────────────────────────────────
live_candidates = []
if _sb:
    try:
        r = _sb.table("live_interview_sessions").select("*").execute()
        sessions = {s["candidate_id"]: s for s in (r.data or [])}
    except Exception:
        sessions = {}
else:
    sessions = {}

all_cands = get_candidates()
live_candidates = [c for c in all_cands if c.get("status") in
                   ("live_interview_sent","live_interview_complete","shortlisted","offered")]

# ── Metrics ──────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Live Sent",     sum(1 for c in all_cands if c.get("status")=="live_interview_sent"))
m2.metric("Completed",     sum(1 for c in all_cands if c.get("status")=="live_interview_complete"))
m3.metric("Post-Live Shortlisted", sum(1 for c in all_cands if c.get("status") in ("offered","advance")))
m4.metric("Post-Live Rejected",    sum(1 for c in all_cands if c.get("status")=="post_live_rejected"))

st.markdown("---")

if not live_candidates:
    st.info("No candidates in the live interview pipeline yet. Send live interview links from Agent 7.")
    st.stop()

st.markdown(f"### {len(live_candidates)} Candidate(s) in Live Interview Pipeline")

reviewer = st.sidebar.text_input("Your Name (Reviewer)", value="HR Manager")

for c in live_candidates:
    cid    = c.get("id","")
    name   = c.get("name","?")
    region = c.get("region","Unknown")
    status = c.get("status","")
    session = sessions.get(cid, {})
    session_id = session.get("id","")
    skey = f"live_score_{cid}"

    with st.expander(f"**{name}** — {region} — {status.replace('_',' ').title()}", expanded=True):

        # Check for existing score
        existing_score = None
        if _sb and session_id:
            try:
                sr = _sb.table("live_interview_scores").select("*").eq("session_id", session_id).limit(1).execute()
                existing_score = sr.data[0] if sr.data else None
            except Exception:
                pass

        if existing_score and skey not in st.session_state:
            st.info("Previous score loaded from database.")
            st.session_state[skey] = {
                "scores":               existing_score.get("scores",{}),
                "total":                existing_score.get("total_score",0),
                "recommendation":       existing_score.get("recommendation","Hold"),
                "summary":              existing_score.get("summary",""),
                "evidence_highlights":  existing_score.get("evidence_highlights",[]),
                "risks":                existing_score.get("risks",[]),
                "compliance_note":      existing_score.get("compliance_note",""),
                "commission_comfort_confirmed": existing_score.get("commission_comfort_confirmed", False),
                "ai_gate_passed":       True,
            }

        # Transcript input
        # Try to get transcript from session
        transcript_default = session.get("transcript","") or session.get("responses","") or ""
        if isinstance(transcript_default, list):
            transcript_default = "\n".join([f"Q: {r.get('question','')} A: {r.get('answer','')}" for r in transcript_default])

        transcript = st.text_area(
            "Paste live interview transcript or responses:",
            value=transcript_default,
            height=150,
            key=f"transcript_{cid}",
            placeholder="Paste the full transcript or key responses from the live interview here…"
        )

        if st.button(f"⚡ Score Live Interview", key=f"score_{cid}", type="primary"):
            if not transcript.strip():
                st.warning("Paste the transcript first.")
            else:
                with st.spinner(f"Scoring {name}'s live interview…"):
                    result = score_live_interview(session_id, name, region, transcript)
                st.session_state[skey] = result
                st.rerun()

        if skey in st.session_state:
            r   = st.session_state[skey]
            rec = r.get("recommendation","—")
            tot = r.get("total",0)
            col = ("green" if "Advance" in rec else "red" if "Reject" in rec else "orange")
            st.markdown(f"### :{col}[{rec}] — Total: **{tot}/35**")

            if r.get("ai_gate_passed"):
                st.success(f"✅ AI Gate passed — all AI dims ≥ {MIN_AI_DIM}")
            else:
                st.warning(f"⚠️ AI Gate not met (min={r.get('ai_gate_min',0)}, required ≥ {MIN_AI_DIM})")

            if r.get("commission_comfort_confirmed"):
                st.success("✅ Commission-only model confirmed in live interview")
            else:
                st.warning("⚠️ Commission comfort not clearly confirmed — probe in offer conversation")

            scores = r.get("scores",{})
            scols  = st.columns(7)
            for i,(k,label) in enumerate(DIM_LABELS.items()):
                v   = scores.get(k,0)
                is_ai = k in AI_DIMS
                bc  = ("#166534" if v>=4 else "#854D0E" if v==3 else "#991B1B")
                scols[i].markdown(
                    f"<div style='text-align:center;background:{bc}15;border:1.5px solid {bc};border-radius:6px;padding:8px'>"
                    f"<div style='font-size:18px;font-weight:700;color:{bc}'>{v}</div>"
                    f"<div style='font-size:9px;color:{bc}'>{'🔬' if is_ai else ''}{label}</div></div>",
                    unsafe_allow_html=True)

            st.caption(r.get("summary",""))
            cnote = r.get("compliance_note","")
            st.success(f"✅ **Compliance** — {cnote}" if cnote else "✅ **Compliance** — Job-relevant evidence only. No protected characteristics considered.")

            c1, c2 = st.columns(2)
            with c1:
                for e in r.get("evidence_highlights",[]): st.success(f"✅ {e}")
            with c2:
                for rk in r.get("risks",[]): st.warning(f"⚠️ {rk}")

            # Decision buttons
            st.markdown("**Post-Live Decision:**")
            hc1, hc2, hc3, hc4 = st.columns(4)
            if hc1.button("📋 Shortlist", key=f"short_{cid}", type="primary"):
                update_candidate_status(cid, "shortlisted", actor=reviewer)
                st.success("Shortlisted for offer stage."); st.rerun()
            if hc2.button("✅ Advance to Offer", key=f"offer_{cid}"):
                update_candidate_status(cid, "offered", actor=reviewer)
                st.success("Advanced to offer!"); st.rerun()
            if hc3.button("⏸ Hold", key=f"hold_{cid}"):
                update_candidate_status(cid, "live_interview_complete", actor=reviewer)
                st.info("Held.")
            if hc4.button("❌ Reject", key=f"rej_{cid}"):
                update_candidate_status(cid, "post_live_rejected", actor=reviewer)
                st.rerun()
