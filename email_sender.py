"""
email_sender.py — SmartSMBAI HR Suite
Sends branded HTML interview invitations and notifications.
"""
import os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

SMTP_HOST=os.getenv("EMAIL_SMTP_HOST","smtp.hostinger.com")
SMTP_PORT=int(os.getenv("EMAIL_SMTP_PORT","465"))
FROM_EMAIL=os.getenv("EMAIL_ADDRESS","info@smartsmbai.com")
FROM_NAME="SmartSMBAI Recruitment"
PASSWORD=os.getenv("EMAIL_PASSWORD","")

PAYMENT_BY_REGION = {
    "Europe":        "SEPA transfer or Stripe (Net-15)",
    "Africa":        "Flutterwave, Paystack, or mobile money (Net-15)",
    "Latin America": "PIX (Brazil), SPEI (Mexico), or Wise/Payoneer (Net-15)",
    "Canada":        "Stripe or Interac e-transfer (Net-15)",
    "USA":           "Stripe or ACH — 1099 independent contractor (Net-15)",
    "Unknown":       "Regional payment method to be confirmed",
}
CONTRACT_BY_REGION = {
    "Europe":        "Employer of Record for full-time partners; otherwise contractor agreement",
    "Africa":        "Employer of Record or local contract review — varies by country",
    "Latin America": "Employer of Record (Brazil); contractor agreement (other markets)",
    "Canada":        "Independent contractor; French materials for Quebec",
    "USA":           "1099 independent contractor",
    "Unknown":       "Contracting structure to be confirmed",
}

def _send(to_email,subject,html):
    try:
        msg=MIMEMultipart("alternative"); msg["Subject"]=subject
        msg["From"]=f"{FROM_NAME} <{FROM_EMAIL}>"; msg["To"]=to_email
        msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP_SSL(SMTP_HOST,SMTP_PORT) as s:
            s.login(FROM_EMAIL,PASSWORD); s.sendmail(FROM_EMAIL,to_email,msg.as_string())
        return True
    except Exception as e:
        print(f"[SMTP] Error: {e}"); return False

def send_interview_invitation(candidate_name,candidate_email,region,questions,deadline,session_id):
    payment=PAYMENT_BY_REGION.get(region,PAYMENT_BY_REGION["Unknown"])
    contract=CONTRACT_BY_REGION.get(region,CONTRACT_BY_REGION["Unknown"])
    qs_html="".join(f"<li style='margin-bottom:14px'><strong>Q{i+1}:</strong> {q}</li>"
                    for i,q in enumerate(questions))
    html=f"""<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
      <div style="background:#1A2B5E;padding:20px 30px;border-radius:8px 8px 0 0">
        <span style="font-size:22px;font-weight:700;color:#fff">Smart</span>
        <span style="font-size:22px;font-weight:700;color:#2563EB">SMB</span>
        <span style="font-size:22px;font-weight:700;color:#fff">AI</span>
        <span style="font-size:12px;color:#BAC8FF;margin-left:12px">Growth Agent Recruitment · {region}</span>
      </div>
      <div style="padding:30px;border:1px solid #eee;border-top:none">
        <h2 style="color:#1A2B5E">Structured Interview — Certified Growth Agent ({region})</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Congratulations — your application has passed our initial screening.
        Please answer the following questions in writing and reply to this email by <strong>{deadline}</strong>.</p>
        <div style="background:#F0F4FF;padding:20px;border-radius:6px;border-left:4px solid #2563EB;margin:20px 0">
          <p style="font-weight:bold;color:#1E40AF;margin-top:0">Interview Questions:</p>
          <ol style="padding-left:20px">{qs_html}</ol>
        </div>
        <div style="background:#F0FDF4;padding:14px;border-radius:6px;margin:16px 0">
          <p style="font-weight:bold;color:#166534;margin:0 0 6px">Good to know — {region}:</p>
          <p style="color:#166534;margin:0;font-size:13px">
          Payment: {payment}<br>Contracting: {contract}
          </p>
        </div>
        <p style="font-size:12px;color:#6B7280">
        <em>Your responses will be reviewed by AI scoring tools and a human recruiter.
        A human makes all final decisions. Please keep each answer under 400 words.</em>
        </p>
        <p>We look forward to hearing from you.<br>
        <strong>SmartSMBAI Recruitment Team</strong><br>info@smartsmbai.com</p>
      </div>
      <div style="background:#F3F4F6;padding:12px 30px;font-size:11px;color:#9CA3AF;border-radius:0 0 8px 8px">
        Session ID: {session_id} · SmartSMBAI — Productized AI for SMBs
      </div></div>"""
    return _send(candidate_email, f"SmartSMBAI Interview Invitation — Growth Agent ({region})", html)

def send_rejection(candidate_name,candidate_email,region):
    html=f"""<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
      <div style="background:#1A2B5E;padding:20px 30px;border-radius:8px 8px 0 0">
        <span style="font-size:22px;font-weight:700;color:#fff">Smart</span>
        <span style="font-size:22px;font-weight:700;color:#2563EB">SMB</span>
        <span style="font-size:22px;font-weight:700;color:#fff">AI</span>
      </div>
      <div style="padding:30px;border:1px solid #eee;border-top:none">
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Thank you for your interest in the SmartSMBAI Certified Growth Agent role ({region}).
        After careful review, we will not be moving forward with your application at this stage.</p>
        <p>We encourage you to apply again in future rounds as we expand to new markets.
        Warm regards,<br><strong>SmartSMBAI Recruitment Team</strong></p>
      </div></div>"""
    return _send(candidate_email, f"Your SmartSMBAI Application — {region}", html)

def send_offer_and_certification(candidate_name,candidate_email,region):
    payment=PAYMENT_BY_REGION.get(region,PAYMENT_BY_REGION["Unknown"])
    html=f"""<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto">
      <div style="background:#1A2B5E;padding:20px 30px;border-radius:8px 8px 0 0">
        <span style="font-size:22px;font-weight:700;color:#fff">Smart</span>
        <span style="font-size:22px;font-weight:700;color:#2563EB">SMB</span>
        <span style="font-size:22px;font-weight:700;color:#fff">AI</span>
      </div>
      <div style="padding:30px;border:1px solid #eee;border-top:none">
        <h2 style="color:#166534">Welcome to SmartSMBAI — Growth Agent ({region})</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>We are pleased to offer you the <strong>Certified Growth Agent</strong> partnership for the <strong>{region}</strong> territory.</p>
        <div style="background:#F0FDF4;padding:16px;border-radius:6px;border-left:4px solid #059669;margin:16px 0">
          <p style="font-weight:bold;color:#166534;margin:0 0 8px">Commission Structure:</p>
          <p style="color:#166534;margin:0;font-size:13px">
          Build fee commission: 15% of one-time build fee per client<br>
          Monthly subscription: 10% for first 12 months per client<br>
          Territory override: 5% on all active subscriptions in your zone<br>
          Payment: {payment}
          </p>
        </div>
        <p><strong>Next step — required before onboarding any client:</strong><br>
        Complete the 4-hour SmartSMBAI Certification course. You will receive the course link separately.
        Certification covers: Catalog Mastery, Low-CAC Acquisition, Setup Checklist, AI product basics,
        prompt fundamentals, troubleshooting paths, integration rules, data privacy, adoption coaching,
        performance metrics, and escalation procedures.</p>
        <p>Partnership terms and contracting details will follow in a separate email.
        <br>Welcome aboard.<br><strong>SmartSMBAI Recruitment Team</strong></p>
      </div></div>"""
    return _send(candidate_email, f"Welcome to SmartSMBAI — Growth Agent Partnership ({region})", html)
