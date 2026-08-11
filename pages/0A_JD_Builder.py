"""Pages/0A_JD_Builder.py — Agent A: Job Description Builder (SmartSMBAI)"""
import streamlit as st, os, anthropic
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="JD Builder — SmartSMBAI", page_icon="📝", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#059669);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#A7F3D0;margin-left:10px'>
Agent A — Job Description Builder · Certified Growth Agent · Region-Specific</span>
</div>""", unsafe_allow_html=True)

REGIONS = ["Europe", "Africa", "Latin America", "Canada", "USA"]
REGION_DETAILS = {
    "Europe":        ("SEPA transfer or Stripe", "EOR or contractor agreement", "local-language support, privacy awareness, and careful contracting"),
    "Africa":        ("Flutterwave, Paystack, or mobile money", "EOR or local contract review", "WhatsApp Business, mobile-first outreach, and local community networks"),
    "Latin America": ("PIX, SPEI, or Wise/Payoneer", "EOR (Brazil) or contractor agreement", "WhatsApp Business, referrals, and local entrepreneur communities"),
    "Canada":        ("Stripe or Interac e-transfer", "Independent contractor (French materials for Quebec)", "bilingual outreach and Canadian chamber networks"),
    "USA":           ("Stripe or ACH", "1099 independent contractor", "U.S. chambers, associations, and commission-based 1099 partnership"),
}

with st.sidebar:
    st.markdown("### JD Settings")
    region    = st.selectbox("Region", REGIONS)
    eeo       = st.text_area("EEO Statement", value=(
        "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
        "race, colour, religion, sex, national origin, age, disability, or any other "
        "protected characteristic. All hiring decisions are based solely on qualifications, "
        "merit, and business need."
    ), height=100)
    generate  = st.button("Generate Job Description", type="primary", use_container_width=True)

st.markdown(f"## Certified Growth Agent — {region}")
st.caption("Commission-based partnership · AI-first SMB platform · Region-specific posting")

pay_method, contract_type, region_ctx = REGION_DETAILS[region]

if generate:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    with st.spinner(f"Generating {region} job description…"):
        resp = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=2000,
            messages=[{"role": "user", "content": f"""Write a publish-ready job posting for SmartSMBAI's Certified Growth Agent role targeting the {region} market.

ROLE: Certified Growth Agent (commission-only partnership, no base salary)
PLATFORM: SmartSMBAI — productized AI systems (receptionists, lead agents, support assistants) for SMBs
COMMISSION: 15% of one-time build fee + 10% monthly subscription (first 12 months per client) + 5% territory override
PAYMENT METHOD: {pay_method}
CONTRACTING: {contract_type}
REGION CONTEXT: {region_ctx}

REQUIREMENTS FROM SMARTSMBAI PLAYBOOK:
- 2+ years B2B sales, SaaS affiliate, marketing agency, or business consulting
- Active local SME chamber, trade organisation, or entrepreneur network connections
- Comfortable with AI tools and prompting — can explain AI value to non-technical buyers
- Can diagnose basic AI output issues and escalate when needed
- Commission-only comfort — understands pipeline management without a base salary
- Completes 4-hour SmartSMBAI certification before onboarding clients

FORMAT: Plain text suitable for direct copy-paste into job board (Indeed/LinkedIn/local boards).
Use bullets, no tables. Include: Who SmartSMBAI Is, What You'll Do, Compensation Structure, What We're Looking For, Good to Know.
End with: To apply: send your background and the local business network you'd bring to info@smartsmbai.com

EEO: {eeo}"""}]
        )
    jd_text = resp.content[0].text
    st.session_state["jd_text"] = jd_text
    st.session_state["jd_region"] = region

if "jd_text" in st.session_state:
    st.markdown("---")
    st.markdown(f"### Generated — {st.session_state.get('jd_region','?')} Job Description")
    st.text_area("Copy and paste into your job board:", value=st.session_state["jd_text"], height=600)
    st.download_button(
        "Download as .txt",
        data=st.session_state["jd_text"],
        file_name=f"SmartSMBAI_Growth_Agent_{st.session_state.get('jd_region','').replace(' ','_')}.txt",
        mime="text/plain",
    )
