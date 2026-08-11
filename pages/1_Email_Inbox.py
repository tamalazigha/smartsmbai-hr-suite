"""Pages/1_Email_Inbox.py — Agent 1: Email Inbox (SmartSMBAI)"""
import streamlit as st, os
from email_agent import run_ingestion_and_save, fetch_new_applications
from database import get_candidates

st.set_page_config(page_title="Email Inbox — SmartSMBAI HR",page_icon="📥",layout="wide")
st.markdown(
    "<div style='padding:12px 16px;background:#065F46;border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>"
    "<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>"
    "<span style='font-size:12px;color:#A7F3D0;margin-left:10px'>"
    "Agent 1 — Email Inbox · Growth Agent Application Ingestion</span></div>",
    unsafe_allow_html=True)

email_ok = bool(os.getenv("EMAIL_ADDRESS") and os.getenv("EMAIL_PASSWORD"))
with st.sidebar:
    st.markdown("### Email Config")
    if email_ok:
        st.success(f"Connected: {os.getenv('EMAIL_ADDRESS')}")
    else:
        st.error("Configure EMAIL_ADDRESS + EMAIL_PASSWORD in .env")

st.markdown("## Fetch New Applications")
mode = st.radio("Mode", ["Live (mark as read)", "Preview only"], horizontal=True)
if st.button("Fetch New Applications", type="primary", disabled=not email_ok):
    with st.spinner("Scanning inbox..."):
        results = run_ingestion_and_save() if "Live" in mode else fetch_new_applications(mark_seen=False)
    if results:
        st.success(f"{len(results)} application(s) found")
        for r in results:
            ext = r.get("extracted", r)
            with st.expander(f"{ext.get('candidate_name','?')} — {ext.get('region','Unknown')}"):
                c1, c2 = st.columns(2)
                c1.metric("Region", ext.get("region", "—"))
                c2.metric("Email", ext.get("candidate_email", "—"))
    else:
        st.info("No new applications found.")

st.markdown("---")
st.markdown("## All Candidates")
REGION_COLORS = {"Europe":"#1E40AF","Africa":"#065F46","Latin America":"#D97706",
    "Canada":"#7C3AED","USA":"#DC2626","Unknown":"#6B7280"}
for region, tc in REGION_COLORS.items():
    cands = [c for c in get_candidates() if c.get("region") == region]
    if cands:
        st.markdown(f"<span style='font-weight:700;color:{tc}'>{region} ({len(cands)})</span>", unsafe_allow_html=True)
        for c in cands:
            st.caption(f"  {c.get('name','?')} · {c.get('email','?')} · {c.get('status','?').replace('_',' ').title()}")
