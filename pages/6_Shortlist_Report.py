"""Pages/6_Shortlist_Report.py — Agent 6: Shortlist Report (SmartSMBAI v2)
Candidate selection + report history + Word export + CV download + offer tracking
+ certification gate + shortlist history section."""
import streamlit as st, pandas as pd, json
from report_agent import (run_shortlist_report, get_shortlisted_candidates, get_report_history,
    generate_word_doc, generate_cv_word_doc, get_candidate_cv, get_offered_candidates,
    mark_as_offered, get_shortlist_history)
from database import get_candidates, get_shortlist_history as db_get_history

st.set_page_config(page_title="Shortlist Report — SmartSMBAI HR",page_icon="📋",layout="wide")
st.markdown("<div style='padding:12px 16px;background:#166534;border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>SmartSMBAI</span>"
    "<span style='font-size:12px;color:#DCFCE7;margin-left:10px'>"
    "Agent 6 — Shortlist Report · Candidate Selection · History · Certification Gate</span></div>",
    unsafe_allow_html=True)

MAX_MEMO=10
REGIONS=["Europe","Africa","Latin America","Canada","USA"]

with st.sidebar:
    region_filter=st.selectbox("Region:",["All Regions"]+REGIONS)
    prepared_by=st.text_input("Prepared by:",value="SmartSMBAI HR")
    reviewer=st.text_input("Your name (offer tracking):",value="HR Manager")
    st.markdown("---")
    st.markdown("**10-candidate limit**")
    st.caption(f"Max {MAX_MEMO} candidates per memo. Filter by region for best results.")
    st.markdown("**Regenerating reports**")
    st.caption("You can generate a report for the same candidate multiple times. Each run is logged separately.")

# Fetch enriched candidates + report history
all_shortlisted_enriched=get_shortlisted_candidates(
    region=None if region_filter=="All Regions" else region_filter)
all_shortlisted_plain=get_candidates(status="shortlisted")
offered=get_candidates(status="offered")+get_candidates(status="certified")
all_ids=[c["id"] for c in all_shortlisted_enriched]
report_history=get_report_history(all_ids)
st.session_state["_report_ids"]=all_ids

m1,m2,m3=st.columns(3)
m1.metric("Shortlisted",len(all_shortlisted_plain))
m2.metric("Offers Extended",len(offered))
m3.metric("Showing in list",len(all_shortlisted_enriched))

if not all_shortlisted_plain and not offered:
    st.info("No shortlisted candidates yet. Review scorecards in Agent 5."); st.stop()

st.markdown("---")
st.markdown("## Select Candidates for This Report")
st.caption("Tick candidates to include. Reports can be re-run for the same candidate at any time.")

def _on_select_all_change():
    new_val=st.session_state.get("rpt_select_all",False)
    for cid in st.session_state.get("_report_ids",[]): st.session_state[f"rpt_chk_{cid}"]=new_val

col_sa,col_info=st.columns([2,5])
with col_sa: st.checkbox("☑ Select All / Deselect All",key="rpt_select_all",on_change=_on_select_all_change)
with col_info:
    if not all_shortlisted_enriched: st.caption("No candidates match the current region filter.")

selected_ids=[]
DIM_H={"sales_track_record":"Sales","local_network_proof":"Network",
        "tech_ai_prompting_readiness":"Tech/AI","ai_troubleshooting_integration_privacy":"Troubleshoot",
        "ai_adoption_metrics_thinking":"Adoption","communication_clarity":"Comms","region_fit":"Region"}

for c in all_shortlisted_enriched:
    cid=c["id"]; name=c.get("name","?"); region=c.get("region","—")
    score_row=c.get("_score",{}); total=score_row.get("total_score",0)
    rec=score_row.get("recommendation") or "Not scored"
    certified=(c.get("status")=="certified")
    cert_badge="✅" if certified else "⏳"
    rec_badge="✅ "+rec if "Advance" in rec else ("🔴 "+rec if "Not" in rec else ("🟡 "+rec if "Hold" in rec else "⚪ "+rec))
    hist=report_history.get(cid,[]); hist_color="#0C447C" if hist else "#5F5E5A"
    hist_badge=f"📋 {len(hist)}× reported — last {hist[0]['at']} by {hist[0]['by']}" if hist else "○ Not yet reported"
    row_l,row_r=st.columns([5,3])
    with row_l:
        checked=st.checkbox(
            f"**{name}** — {region} — {total}/35 {rec_badge}  {cert_badge} {'Certified' if certified else 'Cert pending'}",
            key=f"rpt_chk_{cid}")
        if checked: selected_ids.append(cid)
    with row_r:
        st.markdown(f"<span style='font-size:12px;color:{hist_color}'>{hist_badge}</span>",unsafe_allow_html=True)

st.markdown("---")
n_selected=len(selected_ids)
if n_selected==0:
    st.caption("No candidates selected — tick boxes above or use Select All.")
elif n_selected>MAX_MEMO:
    st.warning(f"**{n_selected} selected** — max {MAX_MEMO} per memo. Top {MAX_MEMO} by score will be included; "
               f"remaining {n_selected-MAX_MEMO} listed in Process Notes. Deselect lower scorers to avoid the cap.")
else:
    st.caption(f"**{n_selected} candidate(s) selected.**")

generate_btn=st.button(
    f"📋  Generate Report for {n_selected} Selected Candidate(s)" if n_selected else "Select at least one candidate above",
    type="primary",disabled=(n_selected==0),use_container_width=True)

if generate_btn and selected_ids:
    with st.spinner(f"Generating SmartSMBAI Growth Agent memo for {min(n_selected,MAX_MEMO)} of {n_selected} candidate(s)…"):
        memo=run_shortlist_report(
            region=None if region_filter=="All Regions" else region_filter,
            prepared_by=prepared_by, candidate_ids=selected_ids)
    if "error" in memo and "candidate_count" not in memo:
        st.error(memo["error"]); st.stop()
    st.session_state["memo"]=memo; st.rerun()

# ── Render memo ──────────────────────────────────────────────────────
if "memo" in st.session_state:
    memo=st.session_state["memo"]
    st.markdown("---")
    gen_at=(memo.get("generated_at","")[:19]).replace("T"," ")
    st.markdown(f"## Growth Agent Shortlist Memo"
        f"<span style='font-size:13px;color:#5F5E5A;margin-left:10px'>"
        f"Generated: {gen_at} · By: {memo.get('prepared_by','')} · {memo.get('candidate_count',0)} candidate(s)</span>",
        unsafe_allow_html=True)
    if memo.get("single_candidate"):
        st.warning("**Single-candidate memo.** Review the scorecard carefully before extending an offer.")
    excluded=memo.get("excluded_candidates",[])
    if excluded:
        st.warning(f"**{len(excluded)} candidate(s) excluded** (over {MAX_MEMO}-cap): {', '.join(excluded)}. "
                   "Run a separate report for them or deselect lower scorers.")
    dw=memo.get("data_warnings",[])
    if dw:
        with st.expander(f"⚠️ {len(dw)} data warning(s)",expanded=True):
            for w in dw: st.warning(w)
    try:
        word_bytes=generate_word_doc(memo)
        safe_label=f"{'_'.join(filter(None,[region_filter.replace(' ','_'),gen_at[:10]]))}"
        st.download_button("📄  Download as Word Document (.docx)",data=word_bytes,
            file_name=f"SmartSMBAI_Shortlist_Memo_{safe_label}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",type="secondary")
    except Exception as e: st.error(f"Word export failed: {e}")
    st.markdown("---")
    st.markdown("### Executive Summary"); st.info(memo.get("executive_summary","—"))
    st.markdown("### Ranked Candidates")
    name_to_id={c.get("name"):c for c in all_shortlisted_plain}
    for cand in memo.get("ranked_candidates",[]):
        rank=cand.get("rank",""); name=cand.get("name","?"); score=cand.get("score",0)
        region_c=cand.get("region","—"); email=cand.get("email","—"); certified=cand.get("certified",False)
        sc=("green" if score>=22 else "orange" if score>=16 else "red")
        cand_record=name_to_id.get(name,{}); cid=cand_record.get("id","")
        with st.expander(f"#{rank}  **{name}** — {region_c}  |  :{sc}[{score}/35]  |  {'✅ Certified' if certified else '⏳ Cert pending'}",expanded=True):
            sc1,sc2,sc3=st.columns(3)
            with sc1: st.markdown("**Key Strength:**"); st.success(cand.get("key_strength","—"))
            with sc2: st.markdown("**Key Concern:**"); st.error(cand.get("key_concern","—"))
            with sc3: st.markdown("**Commission Understanding:**"); st.info(cand.get("commission_model_understanding","—"))
            for e in cand.get("evidence",[]): st.success(f"✅ {e}")
            for r in cand.get("risks",[]): st.error(f"⚠️ {r}")
            fu=cand.get("follow_up_questions",[])
            if fu:
                st.markdown("**Live Interview Follow-Up Questions:**")
                for q in fu: st.markdown(f"- {q}")
            st.caption(f"Email: {email}"); st.markdown("---")
            b1,b2,_=st.columns([2,2,3])
            with b1:
                if cid:
                    cv_text,cover=get_candidate_cv(cid)
                    if cv_text or cover:
                        try:
                            cv_bytes=generate_cv_word_doc(name,region_c,cv_text,cover)
                            st.download_button("📎  Download CV",data=cv_bytes,
                                file_name=f"CV_{name.replace(' ','_')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"cv_dl_{cid}")
                        except Exception as e: st.warning(f"CV export failed: {e}")
                    else: st.caption("No CV on file")
            with b2:
                if cid:
                    offer_notes=st.text_input("Offer notes:",key=f"offer_notes_{cid}",
                        placeholder="Start date, payment method…",label_visibility="collapsed")
                    if st.button("🎁  Mark as Offered",key=f"offer_{cid}",type="primary"):
                        if mark_as_offered(cid,reviewer,offer_notes):
                            st.success(f"Offer recorded for {name}."); del st.session_state["memo"]; st.rerun()
                        else: st.error("Failed — check Supabase connection.")
    if memo.get("recommended_first_hire"):
        st.markdown("---"); st.markdown("### Recommended First Hire")
        st.success(f"**{memo['recommended_first_hire']}**")
    lig=memo.get("live_interview_guidance",[])
    if lig:
        st.markdown("---"); st.markdown("### Consolidated Live Interview Guide")
        for q in lig: st.markdown(f"- {q}")
    cert_status=memo.get("certification_status",[])
    if cert_status:
        st.markdown("---"); st.markdown("### Certification Tracker")
        st.caption("4-hour SmartSMBAI certification must be completed before any client onboarding.")
        for cs in cert_status:
            icon="✅" if cs.get("certified") else "⏳"
            st.markdown(f"{icon} **{cs.get('name','—')}** — {cs.get('action_required','')}")
    if memo.get("process_notes"):
        st.markdown("---"); st.markdown("### Process Notes")
        st.markdown(memo["process_notes"])
    st.markdown("---")
    st.download_button("⬇  Download memo (JSON)",data=json.dumps(memo,indent=2),
        file_name=f"smartsmbai_shortlist_{gen_at[:10]}.json",mime="application/json")

# ── Shortlist History ────────────────────────────────────────────────
st.markdown("---"); st.markdown("## 📅 Shortlist History")
st.caption("Every shortlisting event is permanently recorded here regardless of later status changes.")
with st.expander("Filter history",expanded=False):
    h1,h2=st.columns(2)
    with h1: hist_region=st.selectbox("Region:",["All Regions"]+REGIONS,key="hist_region_filter")
    with h2: hist_search=st.text_input("Search candidate:",key="hist_name_search",placeholder="Type a name…")

history_rows=db_get_history(region=None if hist_region=="All Regions" else hist_region,limit=200)
if hist_search.strip():
    history_rows=[r for r in history_rows if hist_search.strip().lower() in r.get("candidate_name","").lower()]
if not history_rows:
    st.info("No shortlist history yet. History is recorded the next time you click Shortlist in Agent 5.")
else:
    st.caption(f"**{len(history_rows)} event(s)** in the log.")
    summary_rows=[{"Date":(r.get("shortlisted_at") or "")[:16].replace("T"," "),
                   "Candidate":r.get("candidate_name","—"),"Region":r.get("region","—"),
                   "Score":f"{r.get('total_score',0)}/35","AI Rec":r.get("ai_recommendation","—"),
                   "Reviewer":r.get("reviewer","—"),"HR Notes":(r.get("hr_notes") or "—")[:60]}
                  for r in history_rows]
    st.dataframe(pd.DataFrame(summary_rows),use_container_width=True,hide_index=True)
    st.markdown("### Full Detail")
    st.caption("Expand any row to see the complete snapshot captured at shortlisting.")
    for row in history_rows:
        at_h=(row.get("shortlisted_at") or "")[:16].replace("T"," ")
        name_h=row.get("candidate_name","?"); region_h=row.get("region","—")
        total_h=row.get("total_score",0); rec_h=row.get("ai_recommendation","—")
        rev_h=row.get("reviewer","—"); cid_h=str(row.get("candidate_id") or "")
        rc_h="green" if "Advance" in rec_h else ("red" if "Not" in rec_h else "orange")
        with st.expander(f"**{name_h}** — {region_h} — :{rc_h}[{total_h}/35] — Shortlisted {at_h} by {rev_h}",expanded=False):
            scores_h=row.get("scores_breakdown",{})
            if scores_h:
                sc=st.columns(7)
                for i,(k,lbl) in enumerate(DIM_H.items()):
                    v=scores_h.get(k,0); bc="#166534" if v>=4 else ("#D97706" if v==3 else "#DC2626")
                    sc[i].markdown(f"<div style='text-align:center;background:{bc}15;border:1.5px solid {bc};"
                        f"border-radius:6px;padding:6px'><div style='font-size:18px;font-weight:700;color:{bc}'>{v}</div>"
                        f"<div style='font-size:9px;color:{bc}'>{lbl}</div></div>",unsafe_allow_html=True)
            if row.get("ai_summary"): st.markdown(f"**AI Summary:** {row['ai_summary']}")
            ev_h=row.get("evidence_highlights",[]); ri_h=row.get("risks_or_concerns",[])
            if ev_h or ri_h:
                c1h,c2h=st.columns(2)
                with c1h:
                    st.markdown("**Evidence:**")
                    for e in ev_h: st.success(f"✅ {e}")
                with c2h:
                    st.markdown("**Risks:**")
                    for r in ri_h: st.error(f"⚠️ {r}")
            fu_h=row.get("recommended_follow_up",[])
            if fu_h:
                st.markdown("**Follow-Up Questions:**")
                for q in fu_h: st.markdown(f"- {q}")
            m1h,m2h=st.columns(2)
            with m1h:
                st.caption(f"**HR Notes:** {row.get('hr_notes') or '—'}")
                st.caption(f"**Reviewer:** {row.get('reviewer','—')}")
            with m2h:
                st.caption(f"**Email:** {row.get('candidate_email','—')}")
                if row.get("session_id"): st.caption(f"**Session ID:** `{row['session_id']}`")
            # Action buttons
            st.markdown("---")
            ba1,ba2,_=st.columns([2,2,3])
            with ba1:
                if cid_h:
                    cv_t,cv_c=get_candidate_cv(cid_h)
                    if cv_t or cv_c:
                        try:
                            cv_b=generate_cv_word_doc(name_h,region_h,cv_t,cv_c)
                            st.download_button("📎  Download CV",data=cv_b,
                                file_name=f"CV_{name_h.replace(' ','_')}_{at_h[:10]}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"hist_cv_{cid_h}_{at_h}")
                        except Exception as e: st.warning(f"CV export failed: {e}")
                    else: st.caption("No CV on file")
            with ba2:
                if cid_h:
                    offer_n=st.text_input("Offer notes:",key=f"hist_offer_note_{cid_h}_{at_h}",
                        placeholder="Start date, payment…",label_visibility="collapsed")
                    if st.button("🎁  Mark as Offered",key=f"hist_offer_{cid_h}_{at_h}",type="primary"):
                        if mark_as_offered(cid_h,reviewer,offer_n):
                            st.success(f"Offer recorded for {name_h}."); st.rerun()
                        else: st.error("Failed — check Supabase.")

# ── Offer Tracker ────────────────────────────────────────────────────
st.markdown("---"); st.markdown("### Offer Tracker")
fresh_offered=get_offered_candidates(region=None if region_filter=="All Regions" else region_filter)
if fresh_offered:
    rows=[]
    for c in fresh_offered:
        reviews=c.get("human_reviews",[]); latest=reviews[-1] if reviews else {}
        offered_at=(latest.get("reviewed_at") or c.get("created_at") or "—")[:10]
        rows.append({"Candidate":c.get("name","—"),"Region":c.get("region","—"),
                     "Email":c.get("email","—"),"Offered by":latest.get("reviewer_name","—"),
                     "Date":offered_at,"Notes":latest.get("notes","—") or "—"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.caption(f"{len(fresh_offered)} offer(s) extended. Logged to hr_audit_log.")
else:
    st.info("No offers extended yet. Use 'Mark as Offered' on any candidate card above.")
