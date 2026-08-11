"""
scoring_agent.py — Agent 5: Scoring (SmartSMBAI v2)
Batch scoring + DB restore helpers. Uses SmartSMBAI column names throughout.
"""
import os, json, time
from dotenv import load_dotenv
import anthropic
from database import save_interview_score, get_candidates, _sb, _log

load_dotenv()
client=anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL="claude-sonnet-4-6"
SYSTEM_PROMPT=open("system_prompt_scoring.txt").read()

ADVANCE_THRESHOLD=22; MIN_ANY_DIM=2; MIN_AI_DIM=3
AI_DIMENSIONS=["tech_ai_prompting_readiness","ai_troubleshooting_integration_privacy","ai_adoption_metrics_thinking"]
DIM_KEYS=["sales_track_record","local_network_proof","tech_ai_prompting_readiness",
          "ai_troubleshooting_integration_privacy","ai_adoption_metrics_thinking",
          "communication_clarity","region_fit"]

def get_session_for_candidate(candidate_id: str) -> tuple:
    """Return (session_id, responses, questions) for most recent session."""
    if not _sb: return "","",[]
    try:
        res=(_sb.table("interview_sessions").select("*")
             .eq("candidate_id",candidate_id).order("created_at",desc=True).limit(1).execute())
        if res.data:
            row=res.data[0]
            return row.get("id",""),row.get("responses",[]),row.get("questions",[])
        return "","",[]
    except Exception as e: print(f"[Scoring] get_session: {e}"); return "","",[]

def get_existing_score(session_id: str) -> dict | None:
    if not _sb or not session_id: return None
    try:
        res=(_sb.table("interview_scores").select("*")
             .eq("session_id",session_id).order("scored_at",desc=True).limit(1).execute())
        return res.data[0] if res.data else None
    except Exception as e: print(f"[Scoring] get_existing_score: {e}"); return None

def _db_score_to_result(row: dict) -> dict:
    """Convert a DB interview_scores row to the same shape score_interview() returns."""
    scores={k:row.get(k,1) for k in DIM_KEYS}
    return {"scores":scores,"total":row.get("total_score",sum(scores.values())),
            "recommendation":row.get("recommendation","Hold for Human Review"),
            "summary":row.get("summary",""),
            "evidence_highlights":row.get("evidence_highlights",[]),
            "risks_or_concerns":row.get("risks_or_concerns",[]),
            "recommended_follow_up_questions":row.get("recommended_follow_up_questions",[]),
            "compliance_and_fairness_notes":row.get("compliance_and_fairness_notes",""),
            "from_db":True}

def score_interview(session_id: str, candidate_name: str, region: str, responses: list) -> dict:
    answers_text="\n\n".join(
        f"{r.get('question_id','Q?')}: {r.get('question','')}\nANSWER: {r.get('answer','(no answer)')}"
        for r in responses)
    prompt=f"""Score this SmartSMBAI Certified Growth Agent interview.

CANDIDATE: {candidate_name}
REGION: {region}
ADVANCE THRESHOLD: {ADVANCE_THRESHOLD}/35 — no dim <{MIN_ANY_DIM}, no AI dim <{MIN_AI_DIM}

INTERVIEW RESPONSES:
{answers_text[:6000]}

Score 1-5 on the SmartSMBAI Growth Agent rubric:
1. sales_track_record — Demonstrated, quantifiable B2B sales results (1=none, 5=strong specific results)
2. local_network_proof — Named SME chambers/trade orgs/entrepreneur communities (1=generic, 5=specific named)
3. tech_ai_prompting_readiness — CRM, video, cloud tools, AI tool use, prompting, SMB demo ability
4. ai_troubleshooting_integration_privacy — Diagnose AI output issues, integration awareness, data privacy judgment
5. ai_adoption_metrics_thinking — Adoption barriers, post-launch metrics (accuracy, lead capture, bookings, escalation rate)
6. communication_clarity — Answer quality, structure, specificity, tailored to this role
7. region_fit — Specific {region} fit (WhatsApp for Africa/LatAm, French for Quebec, 1099 for USA, SEPA for Europe)

COMMISSION MODEL CHECK: Note whether candidate understands and accepts a commission-only structure.
STRONG SALES + WEAK AI = Hold for Human Review (SmartSMBAI playbook requirement).

Return ONLY valid JSON:
{{
  "sales_track_record": int 1-5,
  "local_network_proof": int 1-5,
  "tech_ai_prompting_readiness": int 1-5,
  "ai_troubleshooting_integration_privacy": int 1-5,
  "ai_adoption_metrics_thinking": int 1-5,
  "communication_clarity": int 1-5,
  "region_fit": int 1-5,
  "recommendation": "Advance" or "Hold for Human Review" or "Do Not Advance",
  "summary": "4-6 sentences — direct assessment for the recruiter",
  "evidence_highlights": ["up to 5 specific evidence quotes or paraphrases"],
  "risks_or_concerns": ["up to 5 specific concerns from the answers"],
  "recommended_follow_up_questions": ["up to 3 questions for the live interview"],
  "compliance_and_fairness_notes": "confirm no protected characteristics used in scoring"
}}

RULES: Advance ≥{ADVANCE_THRESHOLD}, no dim <{MIN_ANY_DIM}, all AI dims ≥{MIN_AI_DIM}.
Strong sales + weak AI = Hold. Never infer protected characteristics."""

    try:
        resp=client.messages.create(model=MODEL,max_tokens=2000,system=SYSTEM_PROMPT,
            messages=[{"role":"user","content":[{"type":"text","text":prompt}]}])
        raw=resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        data=json.loads(raw)
        scores={k:data.get(k,1) for k in DIM_KEYS}
        saved=save_interview_score(session_id=session_id,scores=scores,
            recommendation=data.get("recommendation","Hold for Human Review"),
            summary=data.get("summary",""),evidence=data.get("evidence_highlights",[]),
            risks=data.get("risks_or_concerns",[]),
            follow_up=data.get("recommended_follow_up_questions",[]),
            compliance_note=data.get("compliance_and_fairness_notes",""))
        return {"scores":scores,"total":sum(scores.values()),
                "recommendation":data.get("recommendation","Hold for Human Review"),
                "summary":data.get("summary",""),
                "evidence_highlights":data.get("evidence_highlights",[]),
                "risks_or_concerns":data.get("risks_or_concerns",[]),
                "recommended_follow_up_questions":data.get("recommended_follow_up_questions",[]),
                "compliance_and_fairness_notes":data.get("compliance_and_fairness_notes",""),
                "saved":saved,"from_db":False}
    except Exception as e:
        return {"error":str(e),"recommendation":"Hold for Human Review","summary":f"Scoring error: {e}",
                "scores":{},"total":0,"evidence_highlights":[],"risks_or_concerns":[],
                "recommended_follow_up_questions":[],"from_db":False}

def batch_score_all(status_filter=None,progress_callback=None,skip_already_scored=True) -> dict:
    """Score all candidates in scoring/interview_complete status."""
    if status_filter is None: status_filter=["scoring","interview_complete"]
    seen=set(); candidates=[]
    for s in status_filter:
        for c in get_candidates(status=s):
            if c["id"] not in seen: seen.add(c["id"]); candidates.append(c)
    totals={"processed":0,"skipped":0,"errors":0,"no_responses":0,"results":[]}
    for idx,c in enumerate(candidates):
        cid=c["id"]; name=c.get("name","?"); region=c.get("region","Unknown")
        if progress_callback: progress_callback(idx,len(candidates),name)
        session_id,responses,questions=get_session_for_candidate(cid)
        if not session_id:
            totals["no_responses"]+=1
            totals["results"].append({"candidate":c,"session_id":"","result":{"recommendation":"Hold for Human Review","summary":"No session found.","scores":{},"total":0,"evidence_highlights":[],"risks_or_concerns":[],"recommended_follow_up_questions":[],"error":"no_session"}})
            continue
        if not responses:
            totals["no_responses"]+=1
            totals["results"].append({"candidate":c,"session_id":session_id,"result":{"recommendation":"Hold for Human Review","summary":"No responses yet.","scores":{},"total":0,"evidence_highlights":[],"risks_or_concerns":[],"recommended_follow_up_questions":[],"error":"no_responses"}})
            continue
        if skip_already_scored:
            existing=get_existing_score(session_id)
            if existing:
                totals["skipped"]+=1
                totals["results"].append({"candidate":c,"session_id":session_id,"result":_db_score_to_result(existing)})
                continue
        result=score_interview(session_id,name,region,responses)
        if "error" in result and not result.get("scores"): totals["errors"]+=1
        else: totals["processed"]+=1
        totals["results"].append({"candidate":c,"session_id":session_id,"result":result})
        if idx<len(candidates)-1: time.sleep(0.4)
    if progress_callback: progress_callback(len(candidates),len(candidates),"Done")
    _log("batch_scoring_complete",summary=f"Batch: {totals['processed']} scored, {totals['skipped']} skipped, {totals['no_responses']} no responses, {totals['errors']} errors")
    return totals
