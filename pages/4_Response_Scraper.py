"""Pages/4_Response_Scraper.py — Agent 4: Response Scraper (SmartSMBAI)"""
import streamlit as st, pandas as pd, os
from datetime import datetime, timezone
from response_agent import scan_for_responses
from database import get_candidates

st.set_page_config(page_title="Response Scraper — SmartSMBAI HR", page_icon="📬", layout="wide")
st.markdown(
    "<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#374151);"
    "border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>SmartSMBAI</span>"
    "<span style='font-size:12px;color:#D1D5DB;margin-left:10px'>"
    "Agent 4 — Response Scraper · Auto-Detect · Parse · Score</span></div>",
    unsafe_allow_html=True)

email_ok = bool(os.getenv("EMAIL_ADDRESS") and os.getenv("EMAIL_PASSWORD"))
with st.sidebar:
    if email_ok:
        st.success(f"Connected: {os.getenv('EMAIL_ADDRESS')}")
    else:
        st.error("Configure email in .env")

all_c = get_candidates(); sc = {}
for c in all_c: s = c.get("status","?"); sc[s] = sc.get(s,0)+1
c1,c2,c3 = st.columns(3)
c1.metric("Awaiting Reply", sc.get("interview_sent",0))
c2.metric("Response In", sc.get("interview_complete",0))
c3.metric("In Scoring", sc.get("scoring",0))
st.markdown("---")

pending = [c for c in all_c if c.get("status") == "interview_sent"]
if pending:
    st.markdown("### Pending Replies")
    st.dataframe(pd.DataFrame([{
        "Candidate":c.get("name",""), "Region":c.get("region",""), "Email":c.get("email","")}
        for c in pending]), use_container_width=True, hide_index=True)

st.markdown("---")
col, info = st.columns([1,3])
with col:
    scan_btn = st.button("Scan Inbox Now", type="primary",
                         disabled=not email_ok, use_container_width=True)
with info:
    st.caption("Checks every pending Growth Agent session. Replies are parsed and scored automatically.")

if scan_btn:
    with st.spinner("Scanning info@smartsmbai.com for interview replies..."):
        result = scan_for_responses()
    mc1,mc2,mc3,mc4 = st.columns(4)
    mc1.metric("Checked",  result["sessions_checked"])
    mc2.metric("Found",    result["responses_found"])
    mc3.metric("Scored",   result["processed"])
    mc4.metric("Errors",   result["errors"])
    if result["processed"] > 0:
        st.success(f"{result['processed']} response(s) scored. Go to Agent 5.")
    for d in result.get("details",[]):
        icon = {"processed":"✅","waiting":"⏳","skipped":"⏭","error":"❌"}.get(d["status"],"•")
        if d["status"] == "processed":
            st.success(f"{icon} **{d['candidate_name']}** — {d['message']} (Score: {d.get('score_total',0)}/35)")
        elif d["status"] == "error":
            st.error(f"{icon} **{d['candidate_name']}** — {d['message']}")
        else:
            st.caption(f"{icon} **{d['candidate_name']}** — {d['message']}")
    st.session_state["last_scan"] = datetime.now(timezone.utc).strftime("%d %B %Y %H:%M UTC")

if "last_scan" in st.session_state:
    st.caption(f"Last scan: {st.session_state['last_scan']}")
