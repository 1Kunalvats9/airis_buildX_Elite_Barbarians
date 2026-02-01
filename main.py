import sys
import time
from scraper import run_scrape_cycle
from sheets import get_sheets_service, write_businesses, get_pending_businesses, update_row
from ai import generate_cold_email
from email_sender import extract_email_from_snippet, send_email
from lead_tracker import poll_for_replies
from config import POLL_INTERVAL_SECONDS

def run_scrape_and_store():
    print("\n" + "=" * 60)
    print("  STEP 1: SCRAPING BUSINESSES")
    print("=" * 60 + "\n")

    businesses = run_scrape_cycle()

    if not businesses:
        print("[MAIN] No businesses found this cycle. Try again later.")
        return

    service = get_sheets_service()
    write_businesses(service, businesses)
    print(f"\n[MAIN] Scrape + Store complete. {len(businesses)} businesses processed.\n")


def run_email_pending():
    print("\n" + "=" * 60)
    print("  STEP 2: SENDING EMAILS TO PENDING BUSINESSES")
    print("=" * 60 + "\n")

    service = get_sheets_service()
    pending = get_pending_businesses(service)

    if not pending:
        print("[MAIN] No pending businesses to email.")
        return

    emailed = 0
    skipped = 0

    for biz in pending:
        print(f"\n[MAIN] Processing: {biz['business_name']} ({biz['niche']}, {biz['city']})")
        email_addr = extract_email_from_snippet(biz.get("snippet", ""), biz.get("source_url", ""))

        if not email_addr:
            print(f"  [SKIP] No email address found for '{biz['business_name']}'. Skipping.")
            update_row(service, biz["row_index"],
                       status="No Email Found", email_sent="No",
                       notes="Could not extract email from snippet or URL.")
            skipped += 1
            continue
        
        email_content = generate_cold_email(
            business_name=biz["business_name"],
            niche=biz["niche"],
            city=biz["city"],
            snippet=biz.get("snippet", ""),
        )

        success = send_email(
            to_address=email_addr,
            subject=email_content["subject"],
            body=email_content["body"],
        )

        if success:
            update_row(service, biz["row_index"],
                       status="Contacted", email_sent="Yes",
                       email_address=email_addr,
                       notes=f"Email sent. Subject: {email_content['subject']}")
            emailed += 1
        else:
            update_row(service, biz["row_index"],
                       status="Email Failed", email_sent="No",
                       email_address=email_addr,
                       notes="SMTP send failed. Check logs.")
            skipped += 1

        time.sleep(2) 

    print(f"\n[MAIN] Emailing complete. Sent: {emailed} | Skipped: {skipped}\n")

def run_poll_once():
    print("\n" + "=" * 60)
    print("  STEP 3: POLLING FOR REPLIES")
    print("=" * 60 + "\n")

    poll_for_replies()

def run_poll_loop():
    print("\n" + "=" * 60)
    print(f"  CONTINUOUS POLL MODE (every {POLL_INTERVAL_SECONDS}s)")
    print("=" * 60 + "\n")

    while True:
        poll_for_replies()
        print(f"\n[MAIN] Sleeping {POLL_INTERVAL_SECONDS}s before next poll... (Ctrl+C to stop)\n")
        time.sleep(POLL_INTERVAL_SECONDS)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    print("\nAI CLIENT FINDER AGENT")
    print(f"    Mode: {mode}\n")

    if mode == "scrape":
        run_scrape_and_store()

    elif mode == "email":
        run_email_pending()

    elif mode == "poll":
        run_poll_loop()

    elif mode == "full":
        run_scrape_and_store()
        run_email_pending()
        run_poll_once()

    else:
        print(f"Unknown mode: '{mode}'. Use: full | scrape | email | poll")


if __name__ == "__main__":
    main()