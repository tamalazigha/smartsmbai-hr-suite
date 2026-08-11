"""
response_agent.py — Agent 4: Response Scraper (SmartSMBAI)
Auto-detects interview reply emails, parses answers, triggers scoring.
"""
import os, imaplib, email, re, json
from email.header import decode_header
from datetime import datetime, timezone
from dotenv import load_dotenv
import anthropic
from database import update_session_responses, update_candidate_status, _log, _sb
from interview_agent import parse_interview_responses
from scoring_agent import score_interview

load_dotenv()
IMAP_HOST=os.getenv("EMAIL_IMAP_HOST","imap.hostinger.com")
IMAP_PORT=int(os.getenv("EMAIL_IMAP_PORT","993"))
EMAIL_ADDRESS=os.getenv("EMAIL_ADDRESS",""); EMAIL_PASSWORD=os.getenv("EMAIL_PASSWORD","")
MAILBOX=os.getenv("EMAIL_MAILBOX","INBOX")
client=anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def _decode(v):
    parts=decode_header(v or ""); res=[]
    for p,enc in parts:
        res.append(p.decode(enc or "utf-8",errors="replace") if isinstance(p,bytes) else str(p))
    return " ".join(res)

def _body(msg):
    body=""
    for part in msg.walk():
        if part.get_content_type()=="text/plain" and "attachment" not in str(part.get("Content-Disposition","")):
            pl=part.get_payload(decode=True)
            if pl: body+=pl.decode("utf-8",errors="replace")
    return body.strip()

def _sender_email(from_hdr):
    m=re.search(r"<(.+?)>",from_hdr)
    return m.group(1).strip().lower() if m else from_hdr.strip().lower()

def _pending_sessions():
    if not _sb: return []
    try:
        return (_sb.table("interview_sessions")
                .select("*, candidates(name,email,region)")
                .in_("status",["sent","pending","in_progress"])
                .execute().data or [])
    except Exception as e:
        print(f"[Response] DB error: {e}"); return []

def _is_response(subject,body):
    sl=subject.lower(); bl=body.lower()
    if sl.startswith("re:"): return True
    if re.search(r"\bq[1-9]\b|\b1\.\s|\bquestion [1-9]\b",bl): return True
    if ("answer" in bl or "response" in bl) and len(body)>200: return True
    return False

def scan_for_responses(mark_processed=True) -> dict:
    summary={"sessions_checked":0,"responses_found":0,"processed":0,"errors":0,"details":[]}
    sessions=_pending_sessions()
    if not sessions: return summary
    try:
        imap=imaplib.IMAP4_SSL(IMAP_HOST,IMAP_PORT); imap.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
    except Exception as e:
        summary["errors"]+=1; summary["details"].append({"candidate_name":"—","status":"error","message":f"IMAP failed: {e}"}); return summary

    for sess in sessions:
        summary["sessions_checked"]+=1
        session_id=sess.get("id",""); questions=sess.get("questions",[])
        cand=sess.get("candidates") or {}
        cand_email=cand.get("email",""); cand_name=cand.get("name","?"); cand_region=cand.get("region","Unknown")
        candidate_id=sess.get("candidate_id","")
        if not cand_email:
            summary["details"].append({"candidate_name":cand_name,"status":"skipped","message":"No email"})
            continue
        after_date=None
        invite_at=sess.get("invite_sent_at") or sess.get("created_at")
        if invite_at:
            try:
                dt=datetime.fromisoformat(invite_at.replace("Z","+00:00"))
                after_date=dt.strftime("%d-%b-%Y")
            except: pass
        try:
            imap.select(MAILBOX)
            search=f'(FROM "{cand_email}"' + (f' SINCE "{after_date}"' if after_date else '') + ')'
            _,nums=imap.search(None,search)
            replies=[]
            for num in nums[0].split():
                try:
                    _,data=imap.fetch(num,"(RFC822)")
                    msg=email.message_from_bytes(data[0][1])
                    subj=_decode(msg.get("Subject","")); body_text=_body(msg)
                    replies.append({"subject":subj,"body":body_text,"date":msg.get("Date","")})
                except: pass
        except Exception as e:
            summary["details"].append({"candidate_name":cand_name,"status":"error","message":str(e)}); continue
        if not replies:
            summary["details"].append({"candidate_name":cand_name,"status":"waiting","message":"No reply yet"}); continue
        replies.sort(key=lambda r:r.get("date",""),reverse=True)
        best=replies[0]
        if not _is_response(best["subject"],best["body"]):
            summary["details"].append({"candidate_name":cand_name,"status":"skipped","message":f"Not a response: '{best['subject'][:50]}'"}); continue
        summary["responses_found"]+=1
        try:
            parsed=parse_interview_responses(best["body"],questions)
            update_session_responses(session_id,parsed,status="completed")
            update_candidate_status(candidate_id,"scoring",actor="response_agent")
        except Exception as e:
            summary["errors"]+=1; summary["details"].append({"candidate_name":cand_name,"status":"error","message":f"Parse failed: {e}"}); continue
        try:
            score_result=score_interview(session_id,cand_name,cand_region,parsed)
            rec=score_result.get("recommendation","Hold for Human Review")
        except Exception as e:
            rec="Hold for Human Review"; summary["errors"]+=1
        _log("response_auto_processed",actor="response_agent",object_type="session",
             object_id=session_id,summary=f"{cand_name} — scored: {rec}")
        summary["processed"]+=1
        summary["details"].append({"candidate_name":cand_name,"status":"processed",
            "message":f"Parsed {len(parsed)} answers — {rec}",
            "scoring_recommendation":rec,"score_total":score_result.get("total",0)})
    try: imap.logout()
    except: pass
    return summary
