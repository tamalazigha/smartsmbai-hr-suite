"""Pages/5_Scoring.py — Agent 5: Scoring (SmartSMBAI v2)
Batch scoring + DB restore on load + save_shortlist_history on shortlist."""
import streamlit as st
from scoring_agent import score_interview, batch_score_all, get_session_for_candidate, get_existing_score, _db_score_to_result
from database import get_candidates, update_candidate_status, save_human_review, save_shortlist_history, _sb

st.set_page_config(page_title="Scoring — SmartSMBAI HR",page_icon="📊",layout="wide")
st.markdown("<div style='padding:12px 16px;background:#DC2626;border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>SmartSMBAI</span>"
    "<span style='font-size:12px;color:#FEE2E2;margin-left:10px'>"
    "Agent 5 — Scoring · 7-Dimension Rubric · Advance ≥22/35 · AI dims ≥3 · Batch Mode</span></div>",
    unsafe_allow_html=True)

DIM={"sales_track_record":"Sales","local_network_proof":"Network",
     "tech_ai_prompting_readiness":"Tech/AI","ai_troubleshooting_integration_privacy":"Troubleshoot",
     "ai_adoption_metrics_thinking":"Adoption","communication_clarity":"Comms","region_fit":"Region Fit"}
AI_DIMS={"tech_ai_prompting_readiness","ai_troubleshooting_integration_privacy","ai_adoption_metrics_thinking"}

candidates=get_candidates(status="scoring")+get_candidates(status="interview_complete")
seen_ids=set(); deduped=[]
for c in candidates:
    if c["id"] not in seen_ids: seen_ids.add(c["id"]); deduped.append(c)
candidates=deduped

# On load: restore existing scores from DB so they survive a page refresh
for c in candidates:
    cid=c["id"]; rk=f"sr_{cid}"
    if rk not in st.session_state:
        session_id,_,_=get_session_for_candidate(cid)
        if session_id:
            existing=get_existing_score(session_id)
            if existing: st.session_state[rk]=_db_score_to_result(existing)

with st.sidebar:
    reviewer=st.text_input("Your Name",value="HR Manager")
    st.markdown("---")
    st.markdown("### Batch Scoring")
    skip_scored=st.checkbox("Skip already-scored",value=True)
    score_all_btn=st.button("▶ Score All Pending",type="primary",use_container_width=True,disabled=not candidates)
    st.markdown("---")
    st.caption("Individual 'Score with Claude' buttons on each card let you re-score at any time.")

if not candidates:
    st.info("No candidates ready for scoring. Responses need to arrive via Agent 4 or be logged in Agent 3."); st.stop()

scored_count=sum(1 for c in candidates if f"sr_{c['id']}" in st.session_state)
m1,m2,m3,m4=st.columns(4)
m1.metric("Total Pending",len(candidates)); m2.metric("Scored",scored_count)
m3.metric("Awaiting Score",len(candidates)-scored_count); m4.metric("Shortlisted",len(get_candidates(status="shortlisted")))

st.markdown("---")
if score_all_btn:
    pending_for_batch=[c for c in candidates if not skip_scored or f"sr_{c['id']}" not in st.session_state]
    if not pending_for_batch:
        st.success("All candidates already have scores. Untick 'Skip already-scored' to re-score.")
    else:
        st.markdown(f"### Scoring {len(pending_for_batch)} candidate(s)…")
        bar=st.progress(0); txt=st.empty()
        def _progress(idx,total,name): bar.progress(int(idx/total*100) if total else 100); txt.caption(f"Scoring {idx+1}/{total}: {name}")
        totals=batch_score_all(status_filter=["scoring","interview_complete"],progress_callback=_progress,skip_already_scored=skip_scored)
        bar.progress(100); txt.caption("Done.")
        for entry in totals["results"]:
            cid=entry["candidate"]["id"]
            if entry["result"].get("scores") or entry["result"].get("recommendation"):
                st.session_state[f"sr_{cid}"]=entry["result"]
        bc1,bc2,bc3,bc4=st.columns(4)
        bc1.metric("Scored (new)",totals["processed"]); bc2.metric("Reused from DB",totals["skipped"])
        bc3.metric("No responses",totals["no_responses"]); bc4.metric("Errors",totals["errors"])

st.markdown("---")
st.markdown(f"### Candidate Scorecards ({len(candidates)} total)")

for c in candidates:
    cid=c.get("id",""); name=c.get("name","?"); region=c.get("region","Unknown")
    rk=f"sr_{cid}"; has_result=rk in st.session_state
    r_preview=st.session_state.get(rk,{})
    rec=r_preview.get("recommendation","—") if has_result else "Not yet scored"
    total=r_preview.get("total",0) if has_result else 0
    rc="green" if "Advance" in rec else ("red" if "Not" in rec else ("orange" if "Hold" in rec else "grey"))
    header=(f"**{name}** — {region}  |  :{rc}[{rec}]  |  {total}/35" if has_result
            else f"**{name}** — {region}  |  :grey[Not yet scored]")

    with st.expander(header,expanded=not has_result):
        session_id,responses,questions=get_session_for_candidate(cid)
        if responses:
            with st.expander("Response preview",expanded=False):
                for r in responses[:2]: st.caption(f"**{r.get('question_id','?')}:** {r.get('answer','')[:180]}…")
        elif not has_result:
            st.warning("No interview responses found. Use Agent 4 or log manually in Agent 3.")
        btn_col,_=st.columns([2,5])
        with btn_col:
            btn_label="🔄 Re-score" if has_result else "⚡ Score with Claude"
            if st.button(btn_label,key=f"score_{cid}",disabled=not responses):
                with st.spinner(f"Scoring {name}…"):
                    result=score_interview(session_id,name,region,responses)
                st.session_state[rk]=result; st.rerun()
        if has_result:
            r=st.session_state[rk]
            if r.get("from_db"): st.caption("📂 Score loaded from database (previous session)")
            if r.get("error") and not r.get("scores"):
                st.error(f"Scoring failed: {r.get('summary','')}"); continue
            col_color="green" if "Advance" in r.get("recommendation","") else ("red" if "Not" in r.get("recommendation","") else "orange")
            st.markdown(f"### :{col_color}[{r.get('recommendation','—')}] — Total: **{r.get('total',0)}/35**")
            scores=r.get("scores",{})
            if scores:
                scols=st.columns(7)
                for i,(k,label) in enumerate(DIM.items()):
                    v=scores.get(k,0); bc="#166534" if v>=4 else ("#D97706" if v==3 else "#DC2626")
                    border="3px" if k in AI_DIMS else "1px"; star="★" if k in AI_DIMS else ""
                    scols[i].markdown(f"<div style='text-align:center;background:{bc}15;border:{border} solid {bc};"
                        f"border-radius:6px;padding:6px'><div style='font-size:18px;font-weight:700;color:{bc}'>{v}</div>"
                        f"<div style='font-size:9px;color:{bc}'>{label}{star}</div></div>",unsafe_allow_html=True)
            st.caption("★ = AI dimension — must be ≥3 to advance (SmartSMBAI rule)")
            st.markdown(f"**Summary:** {r.get('summary','')}")
            e1,e2=st.columns(2)
            with e1:
                for e in r.get("evidence_highlights",[]): st.success(f"✅ {e}")
            with e2:
                for rk2 in r.get("risks_or_concerns",[]): st.warning(f"⚠️ {rk2}")
            if r.get("recommended_follow_up_questions"):
                st.markdown("**Live Interview Follow-Ups:**")
                for q in r["recommended_follow_up_questions"]: st.info(f"❓ {q}")
            st.markdown("---")
            notes=st.text_area("Notes / override reason:",key=f"notes_{cid}",height=60,
                               placeholder="Optional — explain any override of the AI recommendation")
            hc1,hc2,hc3=st.columns(3)
            if hc1.button("✅ Shortlist",key=f"short_{cid}",type="primary"):
                save_human_review(cid,reviewer,"scoring","advance",notes)
                update_candidate_status(cid,"shortlisted",actor=reviewer)
                save_shortlist_history(
                    candidate_id=cid, candidate_name=name, candidate_email=c.get("email",""),
                    region=region, reviewer=reviewer, total_score=r.get("total",0),
                    scores_breakdown=r.get("scores",{}),
                    ai_recommendation=r.get("recommendation",""),
                    ai_summary=r.get("summary",""),
                    evidence=r.get("evidence_highlights",[]),
                    risks=r.get("risks_or_concerns",[]),
                    follow_up=r.get("recommended_follow_up_questions",[]),
                    hr_notes=notes or "", session_id=session_id,
                )
                st.success("Shortlisted! History saved. Go to Agent 6 — Shortlist Report."); st.rerun()
            if hc2.button("⏸ Hold",key=f"hold_{cid}"):
                save_human_review(cid,reviewer,"scoring","hold",notes); st.info("Held.")
            if hc3.button("❌ Reject",key=f"rej_{cid}"):
                save_human_review(cid,reviewer,"scoring","reject",notes)
                update_candidate_status(cid,"rejected",actor=reviewer); st.rerun()
