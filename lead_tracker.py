import imaplib
import email
from email.header import decode_header
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD
from ai import classify_reply
from sheets import get_sheets_service, get_contacted_businesses, update_row, add_lead
from email_sender import send_email


IMAP_SERVER = "imap.gmail.com"


def connect_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        print("[TRACKER] Connected to Gmail IMAP.")
        return mail
    except Exception as e:
        print(f"[TRACKER] IMAP connection failed: {e}")
        return None


def decode_subject(subject_raw) -> str:
    parts = decode_header(subject_raw)
    decoded = []
    for part, encoding in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(encoding or "utf-8"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def fetch_unread_emails() -> list[dict]:
    mail = connect_imap()
    if not mail:
        return []

    emails = []
    try:
        mail.select("INBOX")
        _, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        for mail_id in mail_ids:
            _, msg_data = mail.fetch(mail_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    sender  = msg.get("From", "")
                    subject = decode_subject(msg.get("Subject", ""))

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    emails.append({
                        "sender":  sender,
                        "subject": subject,
                        "body":    body,
                    })

            mail.store(mail_id, "+FLAGS", "\\Seen")

    except Exception as e:
        print(f"[TRACKER] Error fetching emails: {e}")
    finally:
        mail.logout()

    print(f"[TRACKER] Fetched {len(emails)} unread email(s).")
    return emails


def match_reply_to_business(email_data: dict, contacted: list[dict]) -> dict | None:
    sender_email = email_data["sender"].lower()
    subject      = email_data["subject"].lower()
    body         = email_data["body"].lower()

    for biz in contacted:
        biz_email = biz.get("email_address", "").lower()
        biz_name  = biz.get("business_name", "").lower()

        if biz_email and biz_email in sender_email:
            return biz

        name_words = biz_name.split()[:2]
        name_short = " ".join(name_words)
        if len(name_short) > 3 and (name_short in subject or name_short in body):
            return biz

    return None


def send_lead_notification(business_name: str, classification: str, reply_body: str):
    subject = f"New Lead Found: {business_name}"
    body = (
        f"Hi! Your AI agent found a new lead.\n\n"
        f"Business: {business_name}\n"
        f"Classification: {classification}\n\n"
        f"Their reply:\n"
        f"---\n"
        f"{reply_body[:500]}\n"
        f"---\n\n"
        f"Check your 'Leads' sheet in Google Sheets for full details."
    )
    send_email(GMAIL_ADDRESS, subject, body)


def poll_for_replies():
    service = get_sheets_service()
    contacted = get_contacted_businesses(service)

    if not contacted:
        print("[TRACKER] No contacted businesses to match against.")
        return

    unread = fetch_unread_emails()
    if not unread:
        print("[TRACKER] No unread emails. Nothing to process.")
        return

    for em in unread:
        print(f"\n[TRACKER] Processing email from: {em['sender']}")

        matched_biz = match_reply_to_business(em, contacted)
        if not matched_biz:
            print("  [SKIP] Couldn't match to any contacted business.")
            continue

        biz_name = matched_biz["business_name"]
        print(f"  [MATCH] Matched to: {biz_name}")

        classification = classify_reply(em["body"], biz_name)

        notes = f"Reply received. Classification: {classification}"
        if classification == "not_interested":
            update_row(service, matched_biz["row_index"], status="Not Interested", email_sent="Yes", notes=notes)
        else:
            update_row(service, matched_biz["row_index"], status="Lead", email_sent="Yes",
                       email_address=matched_biz.get("email_address", ""), notes=notes)

            matched_biz["notes"] = notes
            add_lead(service, matched_biz)

            send_lead_notification(biz_name, classification, em["body"])
            print(f"  [LEAD] {biz_name} is a LEAD!")

    print("\n[TRACKER] Polling cycle complete.")