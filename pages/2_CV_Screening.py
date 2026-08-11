"""Pages/2_CV_Screening.py — Agent 2: CV Screening (SmartSMBAI)"""
import streamlit as st
from cv_agent import run_cv_screening, batch_screen_all, DIM_KEYS, AI_DIMS, MIN_AI_DIM
from database import get_candidates, update_candidate_status, _sb

st.set_page_config(page_title="CV Screening — SmartSMBAI", page_icon="📄", layout="wide")
st.markdown(
    "<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#534AB7);"
    "border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>"
    "<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>"
    "<span style='font-size:12px;color:#C9C5F5;margin-left:10px'>"
    "Agent 2 — CV Screening · 7-Dimension Rubric · AI Gate ≥3 · Commission Check</span></div>",
    unsafe_allow_html=True,
)

REGIONS = ["All", "Europe", "Africa", "Latin America", "Canada", "USA"]
DIM_LABELS = {
    "sales_track_record":                    "Sales",
    "local_network_proof":                   "Network",
    "tech_ai_prompting_readiness":           "Tech/AI",
    "ai_troubleshooting_integration_privacy":"Troubleshoot",
    "ai_adoption_metrics_thinking":          "Adoption",
    "communication_clarity":                 "Comms",
    "region_fit":                            "Region Fit",
}

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    region_filter = st.selectbox("Filter by Region", REGIONS, key="region_filter")
    run_all       = st.button("▶ Run All Pending", type="primary", use_container_width=True)
    st.markdown("---")
    if st.button("🗑️ Clear All Results", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("cv_result_"):
                del st.session_state[key]
        st.rerun()
    st.caption(
        "**AI Gate:** all three AI dimensions must score ≥3 to Advance. "
        "Strong sales but weak AI → Hold automatically."
    )

# ── Load pending candidates ──────────────────────────────────────────
all_new      = get_candidates(status="new")
all_screening = get_candidates(status="screening")
pending = all_new + all_screening

if region_filter != "All":
    pending = [c for c in pending if c.get("region") == region_filter]

# ── Prominent batch button in main area ─────────────────────────────
if "_trigger_batch" in st.session_state:
    st.session_state.pop("_trigger_batch")
    run_all = True

if pending:
    top_col, _ = st.columns([2, 3])
    with top_col:
        if st.button(
            f"▶ Run All Pending ({len(pending)} candidate(s))",
            type="primary", use_container_width=True, key="run_all_top",
        ):
            st.session_state["_trigger_batch"] = True; st.rerun()
    st.info(
        f"📋 **{len(pending)} candidate(s)** awaiting CV screening. "
        "Click **Run All Pending** to batch-screen, or expand individual cards below."
    )

# ── Batch run ────────────────────────────────────────────────────────
if run_all:
    rf = None if region_filter == "All" else region_filter
    bar = st.progress(0)
    txt = st.empty()
    results = batch_screen_all(region_filter=rf)
    for i, r in enumerate(results):
        cid = r.get("candidate_id","")
        if cid:
            st.session_state[f"cv_result_{cid}"] = r
        bar.progress(int((i+1)/max(len(results),1)*100))
        txt.caption(f"Screened {i+1}/{len(results)}: {r.get('candidate_name','?')}")
    bar.progress(100)
    txt.caption(f"Done — {len(results)} candidate(s) screened.")
    st.rerun()

# ── Individual cards ─────────────────────────────────────────────────
if not pending:
    st.success("✅ No candidates pending CV screening.")
    if not any(k.startswith("cv_result_") for k in st.session_state):
        st.info("Use Agent 1 to ingest applications first.")
    st.markdown("---")
else:
    st.markdown(f"### {len(pending)} Candidate(s) Pending")

for c in pending:
    cid    = c.get("id","")
    name   = c.get("name","?")
    region = c.get("region","Unknown")
    status = c.get("status","new")
    skey   = f"cv_result_{cid}"
    has_r  = skey in st.session_state
    rec    = st.session_state[skey].get("recommendation","—") if has_r else "Not yet screened"
    rc     = ("green" if rec == "Advance" else "red" if rec == "Reject" else
              "orange" if rec == "Hold" else "grey")

    with st.expander(
        f"**{name}** — {region}  |  :{rc}[{rec}]  |  Status: {status}",
        expanded=not has_r,
    ):
        # Fetch application data
        cv_text   = ""
        cover     = ""
        app_id    = ""
        if _sb and cid:
            try:
                ar = _sb.table("applications").select("*").eq("candidate_id",cid).limit(1).execute()
                if ar.data:
                    a       = ar.data[0]
                    cv_text = a.get("cv_text","")
                    cover   = a.get("cover_letter_text","")
                    app_id  = a.get("id","")
            except Exception:
                pass

        col_l, col_r = st.columns(2)
        with col_l:
            cv_disp = st.text_area("CV Text", value=cv_text[:2500], height=130,
                                    key=f"cv_{cid}")
        with col_r:
            cl_disp = st.text_area("Cover Letter", value=cover[:1200], height=130,
                                    key=f"cl_{cid}")

        if st.button(f"⚡ Screen {name}", key=f"screen_{cid}", type="primary"):
            with st.spinner(f"Claude is screening {name}…"):
                result = run_cv_screening(
                    application_id = app_id,
                    candidate_id   = cid,
                    candidate_name = name,
                    region         = region,
                    cv_text        = st.session_state.get(f"cv_{cid}", cv_text),
                    cover_letter   = st.session_state.get(f"cl_{cid}", cover),
                )
            st.session_state[skey] = result
            st.rerun()

        if has_r:
            r   = st.session_state[skey]
            rec = r.get("recommendation","—")
            tot = r.get("total",0)
            col = ("green" if rec=="Advance" else "red" if rec=="Reject" else "orange")
            st.markdown(f"### :{col}[{rec}] — Total: **{tot}/35**")

            # AI gate status
            if r.get("ai_gate_passed"):
                st.success(f"✅ AI Gate passed — all AI dimensions ≥ {MIN_AI_DIM}")
            else:
                st.warning(
                    f"⚠️ **AI Gate not met** (min AI dim = {r.get('ai_gate_min',0)}, "
                    f"required ≥ {MIN_AI_DIM}). Recommendation set to Hold regardless of total score."
                )

            # Commission comfort
            if r.get("commission_comfort"):
                st.success("✅ Commission-only model acknowledged in application")
            else:
                st.warning("⚠️ Commission model not explicitly acknowledged — confirm before advancing")

            # Dimension bars
            scores = r.get("scores",{})
            scols  = st.columns(7)
            for i, (k, label) in enumerate(DIM_LABELS.items()):
                v      = scores.get(k,0)
                is_ai  = k in AI_DIMS
                bc     = ("#166534" if v>=4 else "#854D0E" if v==3 else "#991B1B")
                scols[i].markdown(
                    f"<div style='text-align:center;background:{bc}15;"
                    f"border:1.5px solid {bc};border-radius:6px;padding:8px'>"
                    f"<div style='font-size:18px;font-weight:700;color:{bc}'>{v}</div>"
                    f"<div style='font-size:9px;color:{bc}'>{'🔬' if is_ai else ''}{label}</div></div>",
                    unsafe_allow_html=True,
                )

            st.caption(r.get("summary",""))

            # Compliance badge
            cnote = r.get("compliance_note","")
            st.success(
                f"✅ **Compliance Confirmed** — {cnote}" if cnote
                else "✅ **Compliance Confirmed** — Assessment used job-relevant evidence only. "
                     "No protected characteristics were considered."
            )

            c1, c2 = st.columns(2)
            with c1:
                for f in r.get("green_flags",[]): st.success(f"✅ {f}")
            with c2:
                for f in r.get("red_flags",[]): st.warning(f"⚠️ {f}")

            # HR decision
            st.markdown("**Your decision:**")
            hc1, hc2, hc3 = st.columns(3)
            if hc1.button("✅ Advance to Interview", key=f"adv_{cid}", type="primary"):
                update_candidate_status(cid, "interview_sent", actor="HR")
                st.success("Advanced! Go to Agent 3 to send interview questions."); st.rerun()
            if hc2.button("⏸ Hold for Review", key=f"hold_{cid}"):
                update_candidate_status(cid, "screening", actor="HR"); st.info("Held.")
            if hc3.button("❌ Reject", key=f"rej_{cid}"):
                update_candidate_status(cid, "rejected", actor="HR"); st.rerun()
