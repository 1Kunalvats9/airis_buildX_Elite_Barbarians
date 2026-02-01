"""
test_flow.py — Seeding a test lead to verify the full Email -> Reply -> Lead Tracker loop.
"""
import time
from sheets import get_sheets_service, write_businesses, get_pending_businesses, update_row
from email_sender import send_email
from ai import generate_cold_email

TEST_EMAIL = "1kunalvats9@gmail.com"
TEST_BIZ_NAME = f"Test Business {int(time.time())}"

def main():
    service = get_sheets_service()
    
    print(f"--- 1. Creating fake business '{TEST_BIZ_NAME}' in Sheet ---")
    biz_data = [{
        "business_name": TEST_BIZ_NAME,
        "niche": "testing",
        "city": "Internet",
        "source_url": "http://example.com",
        "snippet": "This is a test business to verify the agent flow.",
        "has_website": "No",
        "status": "Pending",
        "email_sent": "No",
        "email_address": TEST_EMAIL,
        "notes": "Test injection"
    }]
    write_businesses(service, biz_data)
    
    print("\n--- 2. Fetching it back to get Row Index ---")
    pending = get_pending_businesses(service)
    target_biz = None
    for b in pending:
        if b["business_name"] == TEST_BIZ_NAME:
            target_biz = b
            break
            
    if not target_biz:
        print("❌ Could not find the test business in 'Pending' rows. Maybe it was already there?")
        return

    print(f"Found at Row {target_biz['row_index']}")

    print("\n--- 3. Generating & Sending Email ---")
    email_content = generate_cold_email(
        business_name=target_biz["business_name"],
        niche=target_biz["niche"],
        city=target_biz["city"],
        snippet=target_biz["snippet"]
    )
    
    # Send
    success = send_email(
        to_address=TEST_EMAIL,
        subject=email_content["subject"],
        body=email_content["body"]
    )
    
    if success:
        print("\n--- 4. Updating Sheet to 'Contacted' ---")
        update_row(service, target_biz["row_index"],
                   status="Contacted", 
                   email_sent="Yes",
                   email_address=TEST_EMAIL,
                   notes=f"Test email sent. Subject: {email_content['subject']}")
        
        print("\n✅ SUCCESS! Now do this:")
        print(f"1. Check inbox for {TEST_EMAIL}")
        print("2. Reply to that email (e.g. 'I am interested in value prop')")
        print("3. Run 'python main.py poll'")
        print("4. Verify it captures the lead and moves row to 'Lead'!")
    else:
        print("❌ Failed to send email.")

if __name__ == "__main__":
    main()
