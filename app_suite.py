"""app_suite.py — SmartSMBAI HR Recruitment Suite"""
import streamlit as st
st.set_page_config(page_title="SmartSMBAI — HR Recruitment Suite",page_icon="🤝",
    layout="wide",initial_sidebar_state="expanded")
st.markdown("""
<div style='padding:16px 22px;background:linear-gradient(135deg,#1A2B5E,#2563EB);
border-radius:8px;border-left:4px solid #059669;margin-bottom:20px'>
<span style='font-size:26px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:26px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:26px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:14px;color:#BAC8FF;margin-left:14px'>
HR Recruitment Suite · Certified Growth Agent · 5 Regions · 6-Agent Pipeline
</span></div>""",unsafe_allow_html=True)
with st.sidebar:
    st.markdown("### Pipeline — Step by Step")
    st.page_link("pages/0A_JD_Builder.py",          label="📝 Agent A — JD Builder",          icon="🅰️")
    st.page_link("pages/0B_Job_Board.py",             label="📋 Agent B — Job Board",            icon="🅱️")
    st.page_link("pages/1_Email_Inbox.py",            label="📥 Agent 1 — Email Inbox",          icon="1️⃣")
    st.page_link("pages/2_CV_Screening.py",           label="📄 Agent 2 — CV Screening",         icon="2️⃣")
    st.page_link("pages/3_Interviews.py",             label="💬 Agent 3 — Bulk Invitations",     icon="3️⃣")
    st.page_link("pages/4_Response_Scraper.py",       label="📬 Agent 4 — Response Scraper",     icon="4️⃣")
    st.page_link("pages/5_Scoring.py",                label="📊 Agent 5 — Scoring",              icon="5️⃣")
    st.page_link("pages/6_Shortlist_Report.py",       label="📋 Agent 6 — Shortlist Report",     icon="6️⃣")
    st.page_link("pages/7_Live_Interview.py",         label="🎙️ Agent 7 — Live Interview",       icon="7️⃣")
    st.page_link("pages/8_Live_Score.py",             label="📊 Agent 8 — Live Score",           icon="8️⃣")
    st.page_link("pages/9_Candidate_Interview.py",    label="🤝 Agent 9 — Candidate Interview",  icon="9️⃣")
    st.markdown("---")
    st.markdown("📧 `info@smartsmbai.com`")
    st.markdown("🗄️ [Supabase Dashboard](https://app.supabase.com)")
from database import get_candidates
candidates=get_candidates()
sc={}
for c in candidates:
    s=c.get("status","?"); sc[s]=sc.get(s,0)+1
col1,col2,col3,col4,col5,col6=st.columns(6)
col1.metric("Total Applications",len(candidates))
col2.metric("In CV Screening",sc.get("screening",0)+sc.get("new",0))
col3.metric("Interview Sent",sc.get("interview_sent",0))
col4.metric("Responses In",sc.get("interview_complete",0)+sc.get("scoring",0))
col5.metric("Shortlisted",sc.get("shortlisted",0))
col6.metric("Rejected",sc.get("rejected",0))
st.markdown("---")
st.markdown("### Applications by Region")
REGIONS=["Europe","Africa","Latin America","Canada","USA","Unknown"]
REGION_COLORS={"Europe":"#1E40AF","Africa":"#065F46","Latin America":"#D97706",
               "Canada":"#7C3AED","USA":"#DC2626","Unknown":"#6B7280"}
reg_counts={r:0 for r in REGIONS}
for c in candidates:
    r=c.get("region","Unknown"); reg_counts[r]=reg_counts.get(r,0)+1
rcols=st.columns(6)
for col,(region,count) in zip(rcols,reg_counts.items()):
    tc=REGION_COLORS.get(region,"#6B7280")
    col.markdown(f"<div style='background:{tc}15;border:2px solid {tc};border-radius:8px;padding:12px;text-align:center'>"
        f"<div style='font-size:22px;font-weight:700;color:{tc}'>{count}</div>"
        f"<div style='font-size:11px;color:{tc};font-weight:600'>{region}</div></div>",unsafe_allow_html=True)
st.markdown("---")
st.markdown("### Pipeline Kanban")
stages=[("📥 Ingested",["new"],"#D1FAE5","#065F46"),
        ("📄 Screening",["screening"],"#EDE9FE","#7C3AED"),
        ("💬 Invited",["interview_sent"],"#FEF3C7","#D97706"),
        ("📬 Responded",["interview_complete","scoring"],"#F3F4F6","#374151"),
        ("✅ Shortlisted",["shortlisted"],"#DCFCE7","#166534"),
        ("❌ Rejected",["rejected"],"#FEE2E2","#DC2626")]
kcols=st.columns(6)
for col,(label,statuses,bg,tc) in zip(kcols,stages):
    count=sum(sc.get(s,0) for s in statuses)
    col.markdown(f"<div style='background:{bg};border:1.5px solid {tc};border-radius:8px;padding:12px;text-align:center'>"
        f"<div style='font-size:22px;font-weight:700;color:{tc}'>{count}</div>"
        f"<div style='font-size:11px;color:{tc};font-weight:600'>{label}</div></div>",unsafe_allow_html=True)
awaiting=sc.get("interview_sent",0); pending=sc.get("scoring",0)+sc.get("interview_complete",0)
if awaiting>0:
    st.markdown("---"); st.info(f"📬 **{awaiting} candidate(s)** awaiting replies. Go to **Agent 4 — Response Scraper**.")
if pending>0:
    st.info(f"📊 **{pending} candidate(s)** ready for scoring. Go to **Agent 5 — Scoring**.")
if candidates:
    st.markdown("---"); st.markdown("### Recent Applications")
    import pandas as pd
    df=pd.DataFrame([{"Name":c.get("name","—"),"Region":c.get("region","—"),
        "Status":c.get("status","—").replace("_"," ").title(),
        "Source":c.get("source","email"),
        "Applied":(c.get("created_at") or "—")[:10]} for c in candidates[:25]])
    st.dataframe(df,use_container_width=True,hide_index=True)
else:
    st.info("No applications yet. Use **Agent 1** to ingest applications from `info@smartsmbai.com`.")
