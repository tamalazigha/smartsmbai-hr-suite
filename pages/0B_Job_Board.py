"""Pages/0B_Job_Board.py — Agent B: Job Board Packages (SmartSMBAI)"""
import streamlit as st

st.set_page_config(page_title="Job Board — SmartSMBAI", page_icon="📋", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#7C3AED);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#DDD6FE;margin-left:10px'>
Agent B — Job Board · Region-by-Region Posting Guide</span>
</div>""", unsafe_allow_html=True)

st.markdown("## Job Board Posting Guide — Certified Growth Agent")
st.caption("Post the job description from Agent A to the boards below. All applications route to info@smartsmbai.com")

st.info("**Subject line to tell candidates:** Application — Growth Agent — [Region] — [Your Name]")

BOARDS = {
    "Europe": [
        ("LinkedIn Jobs", "Senior/professional audience — best fit for this role", "1 free post (sponsored available)", "https://linkedin.com/jobs"),
        ("Indeed", "Broad reach across European markets", "3 free posts/month", "https://indeed.com"),
        ("EuroJobs", "Pan-European niche board", "Free basic posts", "https://eurojobs.com"),
    ],
    "Africa": [
        ("Jobberman", "Nigeria — highest local traffic for Lagos/Abuja roles", "3 free posts/month", "https://jobberman.com"),
        ("BrighterMonday", "Kenya, Uganda, Tanzania", "Free basic posts", "https://brightermonday.com"),
        ("Fuzu", "Multi-country African platform", "Free basic posts", "https://fuzu.com"),
        ("LinkedIn Jobs", "Senior candidates across Africa", "1 free post", "https://linkedin.com/jobs"),
    ],
    "Latin America": [
        ("Indeed", "Broad LatAm reach — strong in Mexico and Brazil", "3 free posts/month", "https://indeed.com"),
        ("LinkedIn Jobs", "Professional/B2B audience", "1 free post", "https://linkedin.com/jobs"),
        ("Computrabajo", "Strong in Colombia, Peru, Chile, Argentina", "Free basic posts", "https://computrabajo.com"),
    ],
    "Canada": [
        ("Indeed Canada", "Highest traffic job board in Canada", "3 free posts/month", "https://ca.indeed.com"),
        ("LinkedIn Jobs", "Professional audience — strong for commission roles", "1 free post", "https://linkedin.com/jobs"),
        ("Workopolis", "Canadian-specific board", "Free basic posts", "https://workopolis.com"),
    ],
    "USA": [
        ("Indeed", "Largest US job board by volume", "3 free posts/month", "https://indeed.com"),
        ("LinkedIn Jobs", "Best for B2B sales and commission roles", "1 free post", "https://linkedin.com/jobs"),
        ("ZipRecruiter", "Strong for commission-based sales roles", "4-day free trial", "https://ziprecruiter.com"),
    ],
}

COLORS = {
    "Europe": "#1E40AF", "Africa": "#065F46", "Latin America": "#D97706",
    "Canada": "#7C3AED", "USA": "#DC2626",
}

for region, boards in BOARDS.items():
    tc = COLORS.get(region, "#374151")
    st.markdown(f"""<div style='background:{tc}10;border-left:4px solid {tc};
    border-radius:6px;padding:10px 16px;margin:16px 0 8px'>
    <span style='font-size:16px;font-weight:700;color:{tc}'>{region}</span></div>""",
    unsafe_allow_html=True)

    cols = st.columns(len(boards))
    for col, (board, desc, free_tier, url) in zip(cols, boards):
        col.markdown(f"""<div style='background:white;border:1px solid #E5E7EB;
        border-radius:8px;padding:12px'>
        <div style='font-weight:700;color:#111827;font-size:14px'>{board}</div>
        <div style='color:#6B7280;font-size:12px;margin:4px 0'>{desc}</div>
        <div style='color:{tc};font-size:12px;font-weight:600'>✓ {free_tier}</div>
        <a href='{url}' target='_blank' style='font-size:11px;color:#2563EB'>Open →</a>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### EEO Notice")
st.caption(
    "Include this at the bottom of every posting: "
    "*SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
    "race, colour, religion, sex, national origin, age, disability, or any other protected characteristic.*"
)
