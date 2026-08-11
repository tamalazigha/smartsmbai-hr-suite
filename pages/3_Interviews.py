"""Pages/3_Interviews.py — Agent 3: Bulk Invitations (SmartSMBAI v2)
Select All fix + duplicate prevention (invite_sent_at tracking)."""
import streamlit as st, pandas as pd
from datetime import datetime, timedelta, timezone
from interview_agent import (run_interview_setup, submit_candidate_responses,
    generate_questions_for_region, get_sessions_for_candidates,
    mark_invite_sent, invitation_already_sent)
from email_sender import send_interview_invitation
from database import get_candidates, update_candidate_status, _sb

st.set_page_config(page_title="Interviews — SmartSMBAI HR",page_icon="💬",layout="wide")
st.markdown("<div style='padding:12px 16px;background:#D97706;border-radius:6px;margin-bottom:16px'>"
    "<span style='font-size:18px;font-weight:700;color:#fff'>SmartSMBAI</span>"
    "<span style='font-size:12px;color:#FEF3C7;margin-left:10px'>"
    "Agent 3 — Bulk Invitations · 12+1 Region-Specific Questions · Duplicate-Safe</span></div>",
    unsafe_allow_html=True)

all_pipeline=[c for c in get_candidates() if c.get("status") in ("interview_sent","screening")]
all_ids=[c["id"] for c in all_pipeline]
session_map=get_sessions_for_candidates(all_ids)
already_invited=[(c,session_map.get(c["id"],{})) for c in all_pipeline if session_map.get(c["id"],{}).get("invite_sent_at")]
ready_to_invite=[(c,session_map.get(c["id"])) for c in all_pipeline if not session_map.get(c["id"],{}).get("invite_sent_at")]
st.session_state["_eligible_ids"]=[c["id"] for c,_ in ready_to_invite]

tab1,tab2=st.tabs(["📤 Send Invitations","📥 Log Responses (Manual)"])

with tab1:
    if not all_pipeline:
        st.info("No candidates in the interview pipeline. Advance candidates from Agent 2."); st.stop()

    if already_invited:
        st.markdown(f"### ✅ Already Invited — {len(already_invited)} candidate(s)")
        st.caption("These candidates have already received an invitation. Use Agent 4 to scan for replies.")
        rows=[{"Candidate":c.get("name","—"),"Region":c.get("region","—"),"Email":c.get("email","—"),
               "Invited":(sess.get("invite_sent_at") or "")[:10],
               "Deadline":(sess.get("deadline") or "")[:10],
               "Response":{"sent":"⏳ Awaiting","completed":"✅ Replied"}.get(sess.get("status",""),"—")}
              for c,sess in already_invited]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    st.markdown("---")
    if not ready_to_invite:
        st.success("All candidates in the pipeline have already been invited."); st.stop()

    st.markdown(f"### ⏳ Ready to Invite — {len(ready_to_invite)} candidate(s)")
    d1,d2=st.columns([2,3])
    with d1: days=st.number_input("Response window (days)",min_value=2,max_value=7,value=3)
    deadline=(datetime.now(timezone.utc)+timedelta(days=int(days))).strftime("%d %B %Y")
    with d2: st.markdown(f"**Deadline:** `{deadline}`")
    st.markdown("---")

    def _on_select_all_change():
        new_val=st.session_state.get("select_all_chk",False)
        for cid in st.session_state.get("_eligible_ids",[]): st.session_state[f"chk_{cid}"]=new_val

    st.checkbox("☑ Select All",key="select_all_chk",on_change=_on_select_all_change)
    selected_ids=[]
    for c,existing_session in ready_to_invite:
        cid=c.get("id",""); region=c.get("region","Unknown")
        pending_note=" _(session created, invite not sent)_" if existing_session and not existing_session.get("invite_sent_at") else ""
        checked=st.checkbox(f"**{c.get('name','?')}** | {region} | {c.get('email','—')}{pending_note}",key=f"chk_{cid}")
        if checked: selected_ids.append(cid)
        with st.expander(f"Preview 13 questions for {region}",expanded=False):
            for i,q in enumerate(generate_questions_for_region(region),1): st.markdown(f"{i}. {q}")

    st.markdown("---")
    if selected_ids: st.caption(f"**{len(selected_ids)} of {len(ready_to_invite)} selected.**")
    send_btn=st.button(f"📨 Send to {len(selected_ids)} Selected" if selected_ids else "Select candidates above",
        type="primary",disabled=not selected_ids,use_container_width=True)

    if send_btn and selected_ids:
        cand_map={c["id"]:(c,sess) for c,sess in ready_to_invite}; rows=[]; bar=st.progress(0)
        for idx,cid in enumerate(selected_ids):
            c,existing_session=cand_map[cid]; region=c.get("region","Unknown")
            if invitation_already_sent(cid):
                rows.append({"Candidate":c.get("name",""),"Region":region,"Email":c.get("email",""),"Status":"⚠️ Skipped — already invited"})
                bar.progress(int((idx+1)/len(selected_ids)*100)); continue
            setup=run_interview_setup(cid,region,deadline)
            session=setup.get("session",{}); session_id=session.get("id","—")
            questions=setup.get("questions",generate_questions_for_region(region))
            sent=send_interview_invitation(c.get("name",""),c.get("email",""),region,questions,deadline,session_id)
            if sent:
                mark_invite_sent(session_id); update_candidate_status(cid,"interview_sent",actor="HR")
                rows.append({"Candidate":c.get("name",""),"Region":region,"Email":c.get("email",""),"Status":"✅ Sent"})
            else:
                rows.append({"Candidate":c.get("name",""),"Region":region,"Email":c.get("email",""),"Status":"❌ Email failed"})
            bar.progress(int((idx+1)/len(selected_ids)*100))
        bar.progress(100)
        sent_n=sum(1 for r in rows if "✅" in r["Status"])
        skipped_n=sum(1 for r in rows if "⚠️" in r["Status"])
        if sent_n: st.success(f"✅ {sent_n} invitation(s) sent.")
        if skipped_n: st.warning(f"⚠️ {skipped_n} skipped — already invited.")
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        if sent_n or skipped_n: st.rerun()

with tab2:
    st.markdown("### Log responses manually")
    opts={f"{c.get('name')} ({c.get('region')})":c for c in get_candidates()
          if c.get("status") in ("interview_sent","interview_complete")}
    if not opts: st.info("No pending interviews."); st.stop()
    sel=st.selectbox("Select candidate",list(opts.keys())); c=opts[sel]; cid=c.get("id","")
    session_id=""; questions=[]
    if _sb:
        try:
            res=_sb.table("interview_sessions").select("*").eq("candidate_id",cid).order("created_at",desc=True).limit(1).execute()
            if res.data: session_id=res.data[0]["id"]; questions=res.data[0].get("questions",[])
        except: pass
    if questions:
        with st.expander("Questions sent to this candidate",expanded=False):
            for i,q in enumerate(questions,1): st.markdown(f"{i}. {q}")
    raw=st.text_area("Paste candidate reply:",height=300)
    if st.button("Parse & Save",type="primary") and raw and session_id:
        responses=submit_candidate_responses(session_id,cid,raw,questions)
        st.success(f"Saved {len(responses)} responses."); update_candidate_status(cid,"scoring",actor="HR")
        st.info("Go to Agent 5 to score, or let Agent 4 handle it automatically.")
