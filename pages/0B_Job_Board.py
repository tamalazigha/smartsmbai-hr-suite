"""Pages/0B_Job_Board.py — Agent B: Job Board Distribution (SmartSMBAI)
Loads JD from library dropdown (no manual paste needed).
Customizes per board using Claude. Downloads per-board packages.
"""
import streamlit as st, os, anthropic
from dotenv import load_dotenv
from jd_agent import get_job_descriptions
from database import _sb

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="Job Board — SmartSMBAI", page_icon="📋", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#7C3AED);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#DDD6FE;margin-left:10px'>
Agent B — Job Board · Load from Library · Board-Specific Customization · Download Packages</span>
</div>""", unsafe_allow_html=True)

REGION_COLORS = {
    "Europe": "#1E40AF", "Africa": "#065F46", "Latin America": "#D97706",
    "Canada": "#7C3AED", "USA": "#DC2626",
}

BOARDS = {
    "Europe": [
        {"name":"LinkedIn Jobs","char_limit":2000,"tone":"professional, concise, achievement-focused",
         "format_rules":"Hook in first 2 sentences. Short bullets. Commission structure front and centre. LinkedIn readers are professionals scanning quickly.",
         "free_tier":"1 free post","url":"https://linkedin.com/talent/post-a-job"},
        {"name":"Indeed","char_limit":5000,"tone":"clear, direct, structured",
         "format_rules":"ALL CAPS section headers (WHO WE ARE, WHAT YOU'LL DO, COMPENSATION, REQUIREMENTS, HOW TO APPLY). Include commission details prominently — Indeed's algorithm favours pay transparency.",
         "free_tier":"3 free posts/month","url":"https://employers.indeed.com"},
        {"name":"EuroJobs","char_limit":3000,"tone":"international-professional",
         "format_rules":"Emphasise European market span. Note remote/async flexibility. Multilingual candidates welcome.",
         "free_tier":"Free basic post","url":"https://eurojobs.com"},
    ],
    "Africa": [
        {"name":"Jobberman","char_limit":3000,"tone":"direct, opportunity-forward, locally grounded",
         "format_rules":"Jobberman is Nigeria's top board. Lead with earning potential. Mention WhatsApp as primary work tool. Cite specific Nigerian cities if relevant.",
         "free_tier":"3 free posts/month","url":"https://jobberman.com/post-a-job"},
        {"name":"BrighterMonday","char_limit":2500,"tone":"professional, East Africa-aware",
         "format_rules":"Covers Kenya, Uganda, Tanzania. Mention mobile-first working and certification track. Keep bullets tight.",
         "free_tier":"Free basic post","url":"https://brightermonday.com"},
        {"name":"LinkedIn Jobs","char_limit":2000,"tone":"professional, diaspora-aware",
         "format_rules":"LinkedIn Africa reaches local and diaspora professionals. Territory override is a strong hook.",
         "free_tier":"1 free post","url":"https://linkedin.com/talent/post-a-job"},
    ],
    "Latin America": [
        {"name":"Indeed LatAm","char_limit":5000,"tone":"warm, opportunity-focused, WhatsApp-aware",
         "format_rules":"Strong across Mexico, Colombia, Argentina. Mention WhatsApp Business explicitly. Commission structures are well understood in LatAm B2B.",
         "free_tier":"3 free posts/month","url":"https://employers.indeed.com"},
        {"name":"Computrabajo","char_limit":2500,"tone":"direct, Spanish-market professional",
         "format_rules":"Strong in Colombia, Peru, Chile, Argentina. Compensation in USD with local equivalent. Remote-friendly framing.",
         "free_tier":"Free basic post","url":"https://computrabajo.com"},
        {"name":"LinkedIn Jobs","char_limit":2000,"tone":"professional, bilingual-aware",
         "format_rules":"150-250 words is the sweet spot. Territory override angle resonates. Clear commission structure required.",
         "free_tier":"1 free post","url":"https://linkedin.com/talent/post-a-job"},
    ],
    "Canada": [
        {"name":"Indeed Canada","char_limit":5000,"tone":"professional, bilingual-aware, compliance-conscious",
         "format_rules":"ALL CAPS section headers. Note Quebec/French adaptation. Mention Interac e-transfer. CASL-compliant outreach framing.",
         "free_tier":"3 free posts/month","url":"https://ca.indeed.com/hire"},
        {"name":"LinkedIn Jobs","char_limit":2000,"tone":"professional, chamber-focused",
         "format_rules":"Territory override and recurring income potential. SmartSMBAI as US-headquartered with Canadian operations builds credibility.",
         "free_tier":"1 free post","url":"https://linkedin.com/talent/post-a-job"},
        {"name":"Workopolis","char_limit":3000,"tone":"straightforward, Canadian-professional",
         "format_rules":"Inclusive bilingual-friendly language. Clear remote commission partnership framing. Contractor structure transparent.",
         "free_tier":"Free basic post","url":"https://workopolis.com"},
    ],
    "USA": [
        {"name":"Indeed USA","char_limit":5000,"tone":"direct, results-oriented, 1099-aware",
         "format_rules":"ALL CAPS section headers. 1099 independent contractor language prominent. Pay-transparency note for CA/CO/NY/WA. Commission breakdown must be specific.",
         "free_tier":"3 free posts/month","url":"https://employers.indeed.com"},
        {"name":"LinkedIn Jobs","char_limit":2000,"tone":"professional, B2B sales-focused",
         "format_rules":"150-250 words. Total earning potential upfront. Chamber + B2B community focus. 1099 commission roles perform well when structure is clear.",
         "free_tier":"1 free post","url":"https://linkedin.com/talent/post-a-job"},
        {"name":"ZipRecruiter","char_limit":3000,"tone":"energetic, opportunity-forward",
         "format_rules":"Benefits first then requirements. Include keywords: B2B sales, commission, AI, SaaS, SMB, chamber, networking. ZipRecruiter AI matching responds to specific skill keywords.",
         "free_tier":"4-day free trial","url":"https://ziprecruiter.com/post-jobs"},
    ],
}

# ── STEP 1: Load JD from library ─────────────────────────────────────
st.markdown("### Step 1 — Select Job Description from Library")

jds = get_job_descriptions()
jd_data = st.session_state.get("distribute_jd")

if jds:
    options = [f"{j.get('role_title','')} — {j.get('created_at','')[:10]}" for j in jds]
    # Pre-select if already loaded
    default_idx = 0
    if jd_data:
        try:
            match = f"{jd_data.get('role_title','')} — {jd_data.get('created_at','')[:10]}"
            if match in options:
                default_idx = options.index(match)
        except Exception:
            pass

    selected = st.selectbox("Choose a saved JD:", options, index=default_idx, key="board_jd_select")
    col_load, col_info = st.columns([1, 3])
    with col_load:
        if st.button("📥 Load this JD", type="primary", use_container_width=True):
            idx = options.index(selected)
            st.session_state["distribute_jd"] = jds[idx]
            jd_data = jds[idx]
            st.rerun()
    with col_info:
        if jd_data:
            region = jd_data.get("location", jd_data.get("region", "Unknown"))
            tc = REGION_COLORS.get(region, "#374151")
            st.markdown(
                f"<div style='background:{tc}10;border-left:4px solid {tc};border-radius:6px;padding:8px 14px;'>"
                f"<span style='font-weight:700;color:{tc}'>Loaded:</span> "
                f"{jd_data.get('role_title','')} · {region} · "
                f"Status: {jd_data.get('status','draft').title()}</div>",
                unsafe_allow_html=True,
            )
else:
    st.warning("No saved JDs found. Go to **Agent A — JD Builder**, generate a JD, and it will auto-save here.")
    st.stop()

if not jd_data:
    st.info("Select a JD above and click **Load this JD** to continue.")
    st.stop()

# ── STEP 2: Select boards ─────────────────────────────────────────────
st.markdown("---")
region     = jd_data.get("location", jd_data.get("region", "Europe"))
full_jd    = jd_data.get("full_jd", "")
jd_id      = jd_data.get("id", "")

if not full_jd:
    st.error("The selected JD has no full_jd text. Regenerate it in Agent A.")
    st.stop()

available_boards = BOARDS.get(region, [])
if not available_boards:
    st.warning(f"No board configurations for region '{region}'. Go to Agent A and regenerate for a valid region.")
    st.stop()

st.markdown(f"### Step 2 — Select Job Boards for {region}")
tc = REGION_COLORS.get(region, "#374151")
st.markdown(
    f"<div style='background:{tc}10;border-left:4px solid {tc};border-radius:6px;padding:8px 14px;margin-bottom:12px'>"
    f"Customizing <b>{jd_data.get('role_title','')}</b> for <b>{region}</b> boards</div>",
    unsafe_allow_html=True,
)

board_names = [b["name"] for b in available_boards]
selected_boards = st.multiselect(
    "Job boards to customize for:", board_names, default=board_names, key="selected_boards"
)

# ── STEP 3: Generate ──────────────────────────────────────────────────
st.markdown("---")
if not selected_boards:
    st.caption("Select at least one job board above.")
    st.stop()

if st.button(
    f"✨ Customize for {len(selected_boards)} Board(s) — Auto-Format with Claude",
    type="primary", use_container_width=True,
):
    boards_to_run = [b for b in available_boards if b["name"] in selected_boards]
    st.session_state["board_results"] = {}
    st.session_state["board_region"]  = region
    progress = st.progress(0)
    for i, board in enumerate(boards_to_run):
        with st.spinner(f"Customizing for {board['name']}…"):
            prompt = f"""Customize this SmartSMBAI job description for {board['name']}.

BASE JD:
{full_jd}

TARGET BOARD: {board['name']}
CHARACTER LIMIT: {board['char_limit']} characters maximum
TONE: {board['tone']}
FORMAT RULES: {board['format_rules']}

Rewrite specifically for {board['name']}. Follow format rules exactly.
Stay within {board['char_limit']} characters.
Keep all commission details (15% build fee, 10% monthly, 5% territory override).
Keep the application instruction: send to info@smartsmbai.com
Output ONLY the ready-to-post job description text — no preamble."""
            try:
                resp = client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                customized = resp.content[0].text.strip()
                st.session_state["board_results"][board["name"]] = {
                    "text":      customized,
                    "chars":     len(customized),
                    "limit":     board["char_limit"],
                    "url":       board["url"],
                    "free_tier": board["free_tier"],
                }
            except Exception as e:
                st.session_state["board_results"][board["name"]] = {"error": str(e)}
        progress.progress(int((i + 1) / len(boards_to_run) * 100))
    progress.progress(100)
    # Mark as posted in DB
    if _sb and jd_id:
        try:
            _sb.table("job_descriptions").update({"status": "active"}).eq("id", jd_id).execute()
        except Exception:
            pass
    st.rerun()

# ── STEP 4: Display results ───────────────────────────────────────────
if "board_results" in st.session_state and st.session_state.get("board_region") == region:
    st.markdown("---")
    st.markdown(f"### Customized Posting Packages — {region}")

    for board_name, result in st.session_state["board_results"].items():
        if "error" in result:
            st.error(f"**{board_name}** — Error: {result['error']}")
            continue

        chars   = result["chars"]
        limit   = result["limit"]
        over    = chars > limit
        pct     = min(chars / limit, 1.0)
        bar_col = "#DC2626" if over else "#059669"

        with st.expander(
            f"**{board_name}** — {chars:,} / {limit:,} chars {'⚠️ OVER LIMIT' if over else '✅'}",
            expanded=True,
        ):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(
                    f"<div style='background:#E5E7EB;border-radius:4px;height:8px'>"
                    f"<div style='background:{bar_col};width:{pct*100:.0f}%;height:8px;border-radius:4px'></div></div>",
                    unsafe_allow_html=True,
                )
            col2.caption(f"✓ {result['free_tier']}")
            col3.markdown(f"[Open board ↗]({result['url']})")

            if over:
                st.warning(f"⚠️ {chars - limit:,} chars over limit — consider trimming before posting.")

            st.text_area(
                f"Copy and paste into {board_name}:",
                value=result["text"], height=350,
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
    st.markdown("### EEO Notice — Include on Every Posting")
    st.code(
        "SmartSMBAI is an equal opportunity employer. We welcome applicants regardless of "
        "race, colour, religion, sex, national origin, age, disability, or any other protected "
        "characteristic. All hiring decisions are based solely on qualifications, merit, and business need.",
        language=None,
    )
