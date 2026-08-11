"""
database.py — SmartSMBAI HR Suite (v2 — full upgrade)
Supabase client + all helper functions. Region-aware throughout.
"""
import os, json
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

_sb = None
try:
    from supabase import create_client
    url=os.getenv("SUPABASE_URL",""); key=os.getenv("SUPABASE_ANON_KEY","")
    if url and key: _sb=create_client(url,key)
except Exception as e: print(f"[DB] Supabase not configured: {e}")

def _log(action,actor="system",object_type=None,object_id=None,summary=None,metadata=None):
    if not _sb: return
    try:
        _sb.table("hr_audit_log").insert({"timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "action":action,"actor":actor,"object_type":object_type,"object_id":object_id,
            "summary":summary,"metadata":metadata or {}}).execute()
    except Exception as e: print(f"[DB] Audit error: {e}")

# ── Candidates ───────────────────────────────────────────────────────
def upsert_candidate(name,email,region="Unknown",source="email",phone=None) -> dict:
    data={"name":name,"email":email,"region":region,"source":source,"phone":phone,"status":"new"}
    if _sb:
        try:
            res=_sb.table("candidates").upsert(data,on_conflict="email").execute()
            row=res.data[0] if res.data else data
            _log("candidate_upserted",summary=f"{name} — {region}",metadata={"email":email})
            return row
        except Exception as e: print(f"[DB] upsert_candidate: {e}")
    return data

def update_candidate_status(candidate_id,status,actor="system"):
    if _sb:
        try:
            _sb.table("candidates").update({"status":status}).eq("id",candidate_id).execute()
            _log("status_changed",actor=actor,object_type="candidate",object_id=candidate_id,summary=f"→ {status}")
        except Exception as e: print(f"[DB] update_status: {e}")

def get_candidates(status=None,region=None) -> list:
    if not _sb: return []
    try:
        q=_sb.table("candidates").select("*").order("created_at",desc=True)
        if status: q=q.eq("status",status)
        if region: q=q.eq("region",region)
        return q.execute().data or []
    except Exception as e: print(f"[DB] get_candidates: {e}"); return []

# ── Applications ─────────────────────────────────────────────────────
def save_application(candidate_id,email_subject,email_body,cv_text,cover_letter,raw_email_uid) -> dict:
    data={"candidate_id":candidate_id,"email_subject":email_subject,"email_body":email_body,
          "cv_text":cv_text,"cover_letter_text":cover_letter,"raw_email_uid":raw_email_uid}
    if _sb:
        try:
            res=_sb.table("applications").upsert(data,on_conflict="raw_email_uid").execute()
            _log("application_saved",object_type="candidate",object_id=candidate_id,summary=email_subject[:60])
            return res.data[0] if res.data else data
        except Exception as e: print(f"[DB] save_application: {e}")
    return data

# ── CV Scores ────────────────────────────────────────────────────────
def save_cv_score(application_id,scores,recommendation,summary,green_flags,red_flags):
    data={"application_id":application_id,
          "sales_track_record":scores.get("sales_track_record",0),
          "local_network_proof":scores.get("local_network_proof",0),
          "tech_ai_prompting_readiness":scores.get("tech_ai_prompting_readiness",0),
          "ai_troubleshooting_integration_privacy":scores.get("ai_troubleshooting_integration_privacy",0),
          "ai_adoption_metrics_thinking":scores.get("ai_adoption_metrics_thinking",0),
          "communication_clarity":scores.get("communication_clarity",0),
          "region_fit":scores.get("region_fit",0),
          "total_score":sum(scores.values()),
          "recommendation":recommendation,"summary":summary,
          "green_flags":green_flags,"red_flags":red_flags}
    if _sb:
        try:
            res=_sb.table("cv_scores").insert(data).execute()
            _log("cv_scored",object_type="application",object_id=application_id,
                 summary=f"{recommendation} — {sum(scores.values())}/35")
            return res.data[0] if res.data else data
        except Exception as e: print(f"[DB] save_cv_score: {e}")
    return data

# ── Interview Sessions ───────────────────────────────────────────────
def create_interview_session(candidate_id,region,questions,deadline) -> dict:
    data={"candidate_id":candidate_id,"region":region,"questions":questions,
          "status":"pending","deadline":deadline}
    if _sb:
        try:
            res=_sb.table("interview_sessions").insert(data).execute()
            _log("session_created",object_type="candidate",object_id=candidate_id,
                 summary=f"Interview session — {region}")
            return res.data[0] if res.data else data
        except Exception as e: print(f"[DB] create_session: {e}")
    return data

def update_session_responses(session_id,responses,status="completed"):
    if _sb:
        try:
            _sb.table("interview_sessions").update({"responses":responses,"status":status}).eq("id",session_id).execute()
            _log("responses_saved",object_type="session",object_id=session_id,summary=f"Session {status}")
        except Exception as e: print(f"[DB] update_responses: {e}")

def get_sessions_for_candidates(candidate_ids: list) -> dict:
    """Bulk-fetch most recent session per candidate. Returns {candidate_id: session_row}."""
    if not _sb or not candidate_ids: return {}
    try:
        res=(_sb.table("interview_sessions").select("*")
             .in_("candidate_id",candidate_ids).order("created_at",desc=True).execute())
        result={}
        for row in (res.data or []):
            cid=row.get("candidate_id","")
            if cid and cid not in result: result[cid]=row
        return result
    except Exception as e: print(f"[DB] get_sessions_for_candidates: {e}"); return {}

# ── Interview Scores ─────────────────────────────────────────────────
def save_interview_score(session_id,scores,recommendation,summary,evidence,risks,follow_up,compliance_note="") -> dict:
    data={"session_id":session_id,
          "sales_track_record":scores.get("sales_track_record",1),
          "local_network_proof":scores.get("local_network_proof",1),
          "tech_ai_prompting_readiness":scores.get("tech_ai_prompting_readiness",1),
          "ai_troubleshooting_integration_privacy":scores.get("ai_troubleshooting_integration_privacy",1),
          "ai_adoption_metrics_thinking":scores.get("ai_adoption_metrics_thinking",1),
          "communication_clarity":scores.get("communication_clarity",1),
          "region_fit":scores.get("region_fit",1),
          "total_score":sum(scores.values()),
          "recommendation":recommendation,"summary":summary,
          "evidence_highlights":evidence,"risks_or_concerns":risks,
          "recommended_follow_up_questions":follow_up,
          "compliance_and_fairness_notes":compliance_note}
    if _sb:
        try:
            res=_sb.table("interview_scores").insert(data).execute()
            _log("interview_scored",object_type="session",object_id=session_id,
                 summary=f"{recommendation} — {sum(scores.values())}/35")
            return res.data[0] if res.data else data
        except Exception as e: print(f"[DB] save_interview_score: {e}")
    return data

# ── Human Reviews ────────────────────────────────────────────────────
def save_human_review(candidate_id,reviewer,stage,decision,notes,override_reason=None):
    data={"candidate_id":candidate_id,"reviewer_name":reviewer,"stage":stage,
          "decision":decision,"notes":notes,"override_reason":override_reason}
    if _sb:
        try:
            _sb.table("human_reviews").insert(data).execute()
            _log("human_review",actor=reviewer,object_type="candidate",object_id=candidate_id,
                 summary=f"{reviewer} → {decision} at {stage}")
        except Exception as e: print(f"[DB] save_human_review: {e}")

# ── Shortlist History ────────────────────────────────────────────────
def save_shortlist_history(candidate_id,candidate_name,candidate_email,region,reviewer,
                           total_score,scores_breakdown,ai_recommendation,ai_summary,
                           evidence,risks,follow_up,hr_notes,session_id=None) -> dict:
    """Save a full point-in-time snapshot when a candidate is shortlisted."""
    data={"candidate_id":candidate_id or None,"candidate_name":candidate_name,
          "candidate_email":candidate_email or "","region":region or "",
          "reviewer":reviewer,"total_score":total_score or 0,
          "scores_breakdown":scores_breakdown or {},"ai_recommendation":ai_recommendation or "",
          "ai_summary":ai_summary or "","evidence_highlights":evidence or [],
          "risks_or_concerns":risks or [],"recommended_follow_up":follow_up or [],
          "hr_notes":hr_notes or "","session_id":session_id or None}
    if _sb:
        try:
            res=_sb.table("shortlist_history").insert(data).execute()
            _log("shortlist_history_saved",actor=reviewer,object_type="candidate",
                 object_id=candidate_id,summary=f"{candidate_name} shortlisted — {region} — {total_score}/35")
            return res.data[0] if res.data else data
        except Exception as e: print(f"[DB] save_shortlist_history: {e}")
    return data

def get_shortlist_history(region=None,candidate_id=None,limit=200) -> list:
    if not _sb: return []
    try:
        q=(_sb.table("shortlist_history").select("*")
           .order("shortlisted_at",desc=True).limit(limit))
        if region: q=q.eq("region",region)
        if candidate_id: q=q.eq("candidate_id",candidate_id)
        return q.execute().data or []
    except Exception as e: print(f"[DB] get_shortlist_history: {e}"); return []
