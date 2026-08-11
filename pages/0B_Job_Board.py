"""Pages/0B_Job_Board.py — Agent B: Job Board Packages (SmartSMBAI)
Takes the JD from Agent A and customizes it for each job board's
specific format, character limits, tone, and requirements.
"""
import streamlit as st, os, anthropic
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Job Board — SmartSMBAI", page_icon="📋", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#7C3AED);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#DDD6FE;margin-left:10px'>
Agent B — Job Board Packages · Board-Specific JD Customization · 5 Regions</span>
</div>""", unsafe_allow_html=True)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

REGIONS = ["Europe", "Africa", "Latin America", "Canada", "USA"]
REGION_COLORS = {
    "Europe": "#1E40AF", "Africa": "#065F46", "Latin America": "#D97706",
    "Canada": "#7C3AED", "USA": "#DC2626",
}

BOARDS = {
    "Europe": [
        {
            "name": "LinkedIn Jobs",
            "char_limit": 2000,
            "tone": "professional, concise, achievement-focused",
            "format_rules": "No tables. Short punchy bullets. Lead with the opportunity and earning potential. LinkedIn readers are professionals scanning quickly — hook them in the first 2 sentences.",
            "free_tier": "1 free post",
            "url": "https://linkedin.com/talent/post-a-job",
        },
        {
            "name": "Indeed",
            "char_limit": 5000,
            "tone": "clear, direct, structured",
            "format_rules": "Indeed supports longer descriptions. Use clear section headers in ALL CAPS (WHO WE ARE, WHAT YOU'LL DO, COMPENSATION, REQUIREMENTS, HOW TO APPLY). Bullets under each section. Include salary/commission details prominently — Indeed's algorithm favours posts with pay info.",
            "free_tier": "3 free posts/month",
            "url": "https://employers.indeed.com",
        },
        {
            "name": "EuroJobs",
            "char_limit": 3000,
            "tone": "international-professional, multi-market aware",
            "format_rules": "Emphasise that the role spans European markets. Mention language flexibility and remote/async work. EuroJobs audience includes multilingual candidates so note if multiple European languages are a bonus.",
            "free_tier": "Free basic post",
            "url": "https://eurojobs.com",
        },
    ],
    "Africa": [
        {
            "name": "Jobberman",
            "char_limit": 3000,
            "tone": "direct, opportunity-forward, locally grounded",
            "format_rules": "Jobberman is Nigeria's top job board. Lead with earning potential in Naira equivalent or USD. Mention WhatsApp as the work tool. Call out specific Nigerian cities if relevant. Candidates respond to clear commission structures with local examples.",
            "free_tier": "3 free posts/month",
            "url": "https://jobberman.com/post-a-job",
        },
        {
            "name": "BrighterMonday",
            "char_limit": 2500,
            "tone": "professional, East African market-aware",
            "format_rules": "BrighterMonday covers Kenya, Uganda, Tanzania. Mention mobile-first working and WhatsApp Business. East African candidates value career growth framing — mention the certification and partner track. Keep bullets tight.",
            "free_tier": "Free basic post",
            "url": "https://brightermonday.com",
        },
        {
            "name": "LinkedIn Jobs (Africa)",
            "char_limit": 2000,
            "tone": "professional, diaspora-aware",
            "format_rules": "LinkedIn Africa reaches both local and diaspora professionals. Emphasise the global platform angle — SmartSMBAI operates internationally. Commission + territory override is a strong hook for LinkedIn Africa audiences.",
            "free_tier": "1 free post",
            "url": "https://linkedin.com/talent/post-a-job",
        },
    ],
    "Latin America": [
        {
            "name": "Indeed LatAm",
            "char_limit": 5000,
            "tone": "warm, opportunity-focused, WhatsApp-aware",
            "format_rules": "Indeed is strong across Mexico, Colombia, Argentina. If the candidate speaks Spanish or Portuguese natively that is a huge plus — say so. Mention WhatsApp Business explicitly as the primary sales channel. Commission structures are well understood in LatAm B2B sales.",
            "free_tier": "3 free posts/month",
            "url": "https://employers.indeed.com",
        },
        {
            "name": "Computrabajo",
            "char_limit": 2500,
            "tone": "direct, Spanish-market professional",
            "format_rules": "Computrabajo is strong in Colombia, Peru, Chile, Argentina. Use clear section headers. Mention that the role is remote-friendly. Compensation in USD with local equivalent makes the post more attractive on this platform.",
            "free_tier": "Free basic post",
            "url": "https://computrabajo.com",
        },
        {
            "name": "LinkedIn Jobs (LatAm)",
            "char_limit": 2000,
            "tone": "professional, bilingual-aware",
            "format_rules": "LinkedIn LatAm audience includes senior sales and business development professionals. Lead with the territory override commission angle — recurring income resonates strongly. Keep it under 300 words for best engagement.",
            "free_tier": "1 free post",
            "url": "https://linkedin.com/talent/post-a-job",
        },
    ],
    "Canada": [
        {
            "name": "Indeed Canada",
            "char_limit": 5000,
            "tone": "professional, bilingual-aware, compliance-conscious",
            "format_rules": "Indeed Canada: use ALL CAPS section headers. Include a note about Quebec/French-language adaptation if relevant. Canadian candidates expect clear commission structures. Mention Interac e-transfer as payment method — it signals local market understanding.",
            "free_tier": "3 free posts/month",
            "url": "https://ca.indeed.com/hire",
        },
        {
            "name": "LinkedIn Jobs (Canada)",
            "char_limit": 2000,
            "tone": "professional, chamber-network focused",
            "format_rules": "LinkedIn Canada: strong for B2B commission sales roles. Lead with the territory override and recurring income potential. Mention that SmartSMBAI is a US-headquartered company with Canadian market operations — this builds credibility.",
            "free_tier": "1 free post",
            "url": "https://linkedin.com/talent/post-a-job",
        },
        {
            "name": "Workopolis",
            "char_limit": 3000,
            "tone": "straightforward, Canadian-professional",
            "format_rules": "Workopolis is a Canadian-specific board. Keep language inclusive and bilingual-friendly. State clearly that this is a remote commission partnership. Canadian audiences respond to transparency about the 1099-equivalent contractor structure.",
            "free_tier": "Free basic post",
            "url": "https://workopolis.com",
        },
    ],
    "USA": [
        {
            "name": "Indeed USA",
            "char_limit": 5000,
            "tone": "direct, results-oriented, 1099-aware",
            "format_rules": "Indeed USA: use ALL CAPS section headers (WHO WE ARE, WHAT YOU'LL DO, COMPENSATION, REQUIREMENTS, HOW TO APPLY). Include the 1099 independent contractor language prominently — US candidates need to know upfront. State pay-transparency note if posting in CA, CO, NY, or WA. Commission breakdown must be specific.",
            "free_tier": "3 free posts/month",
            "url": "https://employers.indeed.com",
        },
        {
            "name": "LinkedIn Jobs (USA)",
            "char_limit": 2000,
            "tone": "professional, B2B sales-focused, concise",
            "format_rules": "LinkedIn USA: 150–250 words is the sweet spot for engagement. Lead with the total earning potential. Mention chamber networks and B2B community focus. 1099 commission roles perform well on LinkedIn when the commission structure is clearly stated upfront.",
            "free_tier": "1 free post",
            "url": "https://linkedin.com/talent/post-a-job",
        },
        {
            "name": "ZipRecruiter",
            "char_limit": 3000,
            "tone": "energetic, opportunity-forward, sales-focused",
            "format_rules": "ZipRecruiter performs well for commission-based sales roles. Use an energetic tone. Bullet the key benefits first, then requirements. ZipRecruiter's AI matching algorithm responds well to specific skill keywords — include: B2B sales, commission, AI, SaaS, SMB, chamber, networking.",
            "free_tier": "4-day free trial",
            "url": "https://ziprecruiter.com/post-jobs",
        },
    ],
}

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Step 1 — Select Region")
    region = st.selectbox("Region to post for", REGIONS)

    st.markdown("### Step 2 — Select Boards")
    available = BOARDS.get(region, [])
    board_names = [b["name"] for b in available]
    selected_boards = st.multiselect("Job boards to customize for:", board_names, default=board_names)

    st.markdown("### Step 3 — Paste Your JD")
    st.caption("Copy the output from Agent A and paste it here, or write your own.")

    generate_all = st.button("✨ Customize for All Selected Boards", type="primary", use_container_width=True)
    st.markdown("---")
    st.info("**Application email:** info@smartsmbai.com\n\n**Subject line to tell candidates:**\nApplication — Growth Agent — [Region] — [Your Name]")

# ── JD Input ─────────────────────────────────────────────────────────
st.markdown(f"## Job Board Packages — {region}")
tc = REGION_COLORS.get(region, "#374151")
st.markdown(f"<div style='background:{tc}10;border-left:4px solid {tc};border-radius:6px;padding:10px 16px;margin-bottom:16px'>"
            f"<span style='font-weight:700;color:{tc}'>{region}</span> · Customizing for: {', '.join(selected_boards) if selected_boards else 'none selected'}</div>",
            unsafe_allow_html=True)

base_jd = st.text_area(
    "Base Job Description (from Agent A):",
    height=200,
    placeholder="Paste the job description generated by Agent A here. If you haven't run Agent A yet, go there first to generate the base JD for this region.",
    key="base_jd",
)

# ── Generate ─────────────────────────────────────────────────────────
if generate_all:
    if not base_jd.strip():
        st.error("Paste the base job description first. Generate it in Agent A.")
    elif not selected_boards:
        st.warning("Select at least one job board.")
    else:
        boards_to_run = [b for b in available if b["name"] in selected_boards]
        st.session_state["board_results"] = {}
        st.session_state["board_region"]  = region

        progress = st.progress(0)
        for i, board in enumerate(boards_to_run):
            with st.spinner(f"Customizing for {board['name']}…"):
                prompt = f"""You are customizing a SmartSMBAI job posting for a specific job board.

BASE JD:
{base_jd}

TARGET BOARD: {board['name']}
CHARACTER LIMIT: {board['char_limit']} characters maximum
TONE: {board['tone']}
FORMAT RULES: {board['format_rules']}

Rewrite the job description specifically for {board['name']}. 
Follow the format rules exactly.
Stay within {board['char_limit']} characters.
Keep all commission details (15% build fee, 10% monthly, 5% territory override).
Keep the application instruction: send to info@smartsmbai.com
Do NOT add any preamble — output ONLY the ready-to-post job description text."""

                try:
                    resp = client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=1500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    customized = resp.content[0].text.strip()
                    char_count = len(customized)
                    st.session_state["board_results"][board["name"]] = {
                        "text": customized,
                        "chars": char_count,
                        "limit": board["char_limit"],
                        "url":   board["url"],
                        "free_tier": board["free_tier"],
                    }
                except Exception as e:
                    st.session_state["board_results"][board["name"]] = {"error": str(e)}

            progress.progress(int((i + 1) / len(boards_to_run) * 100))

        progress.progress(100)
        st.rerun()

# ── Display results ───────────────────────────────────────────────────
if "board_results" in st.session_state and st.session_state.get("board_region") == region:
    st.markdown("---")
    st.markdown(f"### Customized Postings — {region}")

    for board_name, result in st.session_state["board_results"].items():
        if "error" in result:
            st.error(f"**{board_name}** — Error: {result['error']}")
            continue

        chars   = result["chars"]
        limit   = result["limit"]
        url     = result["url"]
        tier    = result["free_tier"]
        over    = chars > limit
        pct     = min(chars / limit, 1.0)
        bar_col = "#DC2626" if over else "#059669"

        with st.expander(f"**{board_name}** — {chars:,} / {limit:,} chars {'⚠️ OVER LIMIT' if over else '✅'}", expanded=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"<div style='background:#E5E7EB;border-radius:4px;height:8px;margin-bottom:8px'>"
                            f"<div style='background:{bar_col};width:{pct*100:.0f}%;height:8px;border-radius:4px'></div></div>",
                            unsafe_allow_html=True)
            col2.caption(f"✓ {tier}")
            col3.markdown(f"[Open board ↗]({url})")

            if over:
                st.warning(f"⚠️ This version is {chars - limit:,} characters over the {board_name} limit. Consider trimming or click Regenerate.")

            st.text_area(
                f"Copy and paste into {board_name}:",
                value=result["text"],
                height=350,
                key=f"output_{board_name}_{region}",
            )
            st.download_button(
                f"⬇️ Download {board_name} version",
                data=result["text"],
                file_name=f"SmartSMBAI_{region.replace(' ','_')}_{board_name.replace(' ','_')}.txt",
                mime="text/plain",
                key=f"dl_{board_name}_{region}",
            )

    st.markdown("---")
    st.markdown("### EEO Notice — Add to Every Posting")
    st.code(
        "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
        "race, colour, religion, sex, national origin, age, disability, or any other protected characteristic. "
        "All hiring decisions are based solely on qualifications, merit, and business need.",
        language=None,
    )
else:
    if not base_jd.strip():
        st.info("👆 First, go to **Agent A — JD Builder** to generate your base job description for this region. Then paste it above and click Customize.")

