"""
email_agent.py — Agent 1: Email Ingestion (SmartSMBAI)
Polls inbox for Growth Agent applications. Region-aware extraction.
"""
import os, imaplib, email, json, re, io
from email.header import decode_header
from dotenv import load_dotenv
import anthropic
load_dotenv()

IMAP_HOST=os.getenv("EMAIL_IMAP_HOST","imap.hostinger.com")
IMAP_PORT=int(os.getenv("EMAIL_IMAP_PORT","993"))
EMAIL_ADDRESS=os.getenv("EMAIL_ADDRESS","")
EMAIL_PASSWORD=os.getenv("EMAIL_PASSWORD","")
MAILBOX=os.getenv("EMAIL_MAILBOX","INBOX")
MODEL="claude-sonnet-4-6"
client=anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SYSTEM_PROMPT=open("system_prompt_email.txt").read()
VALID_REGIONS=["Europe","Africa","Latin America","Canada","USA","Unknown"]

def _decode_hdr(v):
    parts=decode_header(v or ""); res=[]
    for p,enc in parts:
        res.append(p.decode(enc or "utf-8",errors="replace") if isinstance(p,bytes) else p)
    return " ".join(res)

def _parse_attachment(part):
    fn=(part.get_filename() or "").lower(); data=part.get_payload(decode=True)
    if not data: return ""
    if fn.endswith(".pdf"):
        try:
            import pypdf; reader=pypdf.PdfReader(io.BytesIO(data))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except: return "[PDF parse error]"
    if fn.endswith((".docx",".doc")):
        try:
            from docx import Document; doc=Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except: return "[DOCX parse error]"
    if fn.endswith(".txt"):
        return data.decode("utf-8",errors="replace")
    return ""

def _parse_message(msg):
    subject=_decode_hdr(msg.get("Subject",""))
    from_raw=_decode_hdr(msg.get("From",""))
    em=re.search(r"<(.+?)>",from_raw); sender_email=(em.group(1) if em else from_raw).strip().lower()
    sender_name=re.sub(r"<.+?>","",from_raw).strip().strip('"')
    body=""; cv_text=""
    for part in msg.walk():
        ct=part.get_content_type(); disp=str(part.get("Content-Disposition",""))
        if "attachment" in disp or "inline" in disp:
            cv_text+=_parse_attachment(part)
        elif ct=="text/plain" and "attachment" not in disp:
            pl=part.get_payload(decode=True)
            if pl: body+=pl.decode("utf-8",errors="replace")
    return {"subject":subject,"sender_name":sender_name or "Unknown",
            "sender_email":sender_email,"body":body.strip(),"cv_text":cv_text.strip()}

def _extract_data(parsed):
    prompt=f"""Extract structured data from this SmartSMBAI Growth Agent application email.

SUBJECT: {parsed['subject']}
FROM: {parsed['sender_name']} <{parsed['sender_email']}>
BODY: {parsed['body'][:3000]}
CV TEXT: {parsed['cv_text'][:4000]}

Return ONLY valid JSON:
{{
  "candidate_name": string,
  "candidate_email": string,
  "phone": string or null,
  "region": one of ["Europe","Africa","Latin America","Canada","USA","Unknown"],
  "cover_letter": string (max 400 words — extracted or summarised from email body),
  "cv_summary": string (max 400 words — summarised from CV/attachment text),
  "is_application": boolean (true if this is a genuine Growth Agent application)
}}

Infer region from: country mentioned, language used, WhatsApp mention (Africa/LatAm), specific cities, payment methods mentioned."""
    try:
        resp=client.messages.create(model=MODEL,max_tokens=1200,system=SYSTEM_PROMPT,
            messages=[{"role":"user","content":[{"type":"text","text":prompt}]}])
        raw=resp.content[0].text.strip().replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        return {"candidate_name":parsed["sender_name"],"candidate_email":parsed["sender_email"],
                "phone":None,"region":"Unknown","cover_letter":parsed["body"][:400],
                "cv_summary":parsed["cv_text"][:400],"is_application":True,"_error":str(e)}

def fetch_new_applications(mark_seen=True):
    results=[]
    try:
        imap=imaplib.IMAP4_SSL(IMAP_HOST,IMAP_PORT); imap.login(EMAIL_ADDRESS,EMAIL_PASSWORD)
        imap.select(MAILBOX); _,nums=imap.search(None,"UNSEEN")
        for num in nums[0].split():
            try:
                _,data=imap.fetch(num,"(RFC822 UID)")
                uid_str=data[0][0].decode() if data[0][0] else ""; uid_m=re.search(r"UID (\d+)",uid_str)
                uid=uid_m.group(1) if uid_m else num.decode()
                msg=email.message_from_bytes(data[0][1]); parsed=_parse_message(msg)
                extracted=_extract_data(parsed)
                if extracted.get("is_application",False):
                    results.append({"raw_email_uid":uid,"parsed":parsed,"extracted":extracted})
                    if mark_seen: imap.store(num,"+FLAGS","\\Seen")
            except Exception as e:
                print(f"[Email] Error: {e}")
        imap.logout()
    except Exception as e:
        print(f"[Email] IMAP error: {e}")
    return results

def run_ingestion_and_save():
    from database import upsert_candidate, save_application
    apps=fetch_new_applications(); saved=[]
    for app in apps:
        ext=app["extracted"]; parsed=app["parsed"]
        try:
            candidate=upsert_candidate(name=ext.get("candidate_name","Unknown"),
                email=ext.get("candidate_email",""),region=ext.get("region","Unknown"),
                source="email",phone=ext.get("phone"))
            application=save_application(candidate_id=candidate.get("id",""),
                email_subject=parsed.get("subject",""),email_body=parsed.get("body",""),
                cv_text=ext.get("cv_summary","")+"\n\n"+parsed.get("cv_text",""),
                cover_letter=ext.get("cover_letter",""),raw_email_uid=app["raw_email_uid"])
            saved.append({"candidate":candidate,"application":application,"extracted":ext})
        except Exception as e:
            print(f"[Email] Save error: {e}")
    return saved
