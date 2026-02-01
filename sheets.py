import os

# THIS MUST BE SET BEFORE any google-auth / oauthlib code runs.
# It tells oauthlib to allow http:// redirects (localhost is not https).
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, SHEET_ALL_BUSINESSES, SHEET_LEADS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

TOKEN_FILE = "token.json"


def get_sheets_service():
    creds = None
    try:
        with open(TOKEN_FILE, "r") as f:
            creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)
    except (FileNotFoundError, ValueError, KeyError):
        pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            try:
                # Use localhost to allow the OS to resolve to IPv4 or IPv6 as needed by the browser
                creds = flow.run_local_server(port=8080)
            except AttributeError as e:
                if "last_request_uri" in str(e) or "replace" in str(e):
                    print("\n[SHEETS] The browser was redirected but this app didn't receive it")
                    print("(e.g. 'localhost refused to connect'). You can paste the URL to continue.\n")
                    print("Paste the FULL URL from your browser's address bar")
                    print("(the one that starts with http://localhost:8080/ and contains &code=...):")
                    url = input().strip()
                    if not url or "code=" not in url:
                        raise SystemExit("No valid URL pasted. Run the script again and paste the redirect URL.")
                    flow.fetch_token(authorization_response=url)
                    creds = flow.credentials
                else:
                    raise

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)
    print("[SHEETS] Authenticated successfully.")
    return service


HEADERS = [
    "Business Name",
    "Niche",
    "City",
    "Source URL",
    "Snippet",
    "Has Website",
    "Status",
    "Email Sent",
    "Email Address",
    "Notes",
]


def ensure_sheet_exists(service, sheet_name: str):
    metadata = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
    sheets = metadata.get("sheets", [])
    existing_titles = [s['properties']['title'] for s in sheets]

    if sheet_name not in existing_titles:
        print(f"[SHEETS] Creating missing tab: '{sheet_name}'")
        body = {
            "requests": [{
                "addSheet": {
                    "properties": {"title": sheet_name}
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body=body
        ).execute()


def ensure_headers(service, sheet_name: str):
    ensure_sheet_exists(service, sheet_name)

    sheet_quoted = f"'{sheet_name}'" if " " in sheet_name else sheet_name
    
    result = service.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"{sheet_quoted}!A1:A1"
    ).execute()

    if not result.get("values"):
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"{sheet_quoted}!A1",
            valueInputOption="RAW",
            body={"values": [HEADERS]}
        ).execute()
        print(f"[SHEETS] Headers written to '{sheet_name}'")


def write_businesses(service, businesses: list[dict]):
    if not businesses:
        print("[SHEETS] No businesses to write.")
        return

    ensure_headers(service, SHEET_ALL_BUSINESSES)
    existing = get_all_business_names(service)

    rows_to_add = []
    for b in businesses:
        if b["business_name"].lower() in existing:
            print(f"  [SKIP] '{b['business_name']}' already in sheet")
            continue

        row = [
            b.get("business_name", ""),
            b.get("niche", ""),
            b.get("city", ""),
            b.get("source_url", ""),
            b.get("snippet", ""),
            b.get("has_website", "No"),
            b.get("status", "Pending"),
            b.get("email_sent", "No"),
            b.get("email_address", ""),
            b.get("notes", ""),
        ]
        rows_to_add.append(row)

    if rows_to_add:
        service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"'{SHEET_ALL_BUSINESSES}'!A:J",
            valueInputOption="RAW",
            body={"values": rows_to_add}
        ).execute()
        print(f"[SHEETS] Added {len(rows_to_add)} new business(es).")
    else:
        print("[SHEETS] All businesses already exist. Nothing added.")


def get_all_business_names(service) -> set[str]:
    result = service.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_ALL_BUSINESSES}'!A2:A1000"
    ).execute()
    values = result.get("values", [])
    return {row[0].lower() for row in values if row}


def get_pending_businesses(service) -> list[dict]:
    result = service.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_ALL_BUSINESSES}'!A2:J1000"
    ).execute()

    rows = result.get("values", [])
    pending = []
    for i, row in enumerate(rows):
        row += [""] * (10 - len(row))
        if row[6].strip().lower() == "pending":
            pending.append({
                "row_index": i + 2,
                "business_name": row[0],
                "niche":         row[1],
                "city":          row[2],
                "source_url":    row[3],
                "snippet":       row[4],
                "status":        row[6],
            })
    print(f"[SHEETS] Found {len(pending)} pending business(es).")
    return pending


def update_row(service, row_index: int, status: str, email_sent: str, email_address: str = "", notes: str = ""):
    service.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_ALL_BUSINESSES}'!G{row_index}:J{row_index}",
        valueInputOption="RAW",
        body={"values": [[status, email_sent, email_address, notes]]}
    ).execute()
    print(f"[SHEETS] Row {row_index} updated -> Status: {status}")


def add_lead(service, business: dict):
    ensure_headers(service, SHEET_LEADS)

    row = [
        business.get("business_name", ""),
        business.get("niche", ""),
        business.get("city", ""),
        business.get("source_url", ""),
        business.get("snippet", ""),
        business.get("has_website", "No"),
        "Lead",
        business.get("email_sent", "Yes"),
        business.get("email_address", ""),
        business.get("notes", ""),
    ]

    service.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_LEADS}'!A:J",
        valueInputOption="RAW",
        body={"values": [row]}
    ).execute()
    print(f"[SHEETS] Lead added: {business.get('business_name')}")


def get_contacted_businesses(service) -> list[dict]:
    result = service.spreadsheets().values().get(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SHEET_ALL_BUSINESSES}'!A2:J1000"
    ).execute()

    rows = result.get("values", [])
    contacted = []
    for i, row in enumerate(rows):
        row += [""] * (10 - len(row))
        if row[6].strip().lower() == "contacted":
            contacted.append({
                "row_index":     i + 2,
                "business_name": row[0],
                "niche":         row[1],
                "city":          row[2],
                "source_url":    row[3],
                "snippet":       row[4],
                "email_address": row[8],
                "notes":         row[9],
            })
    return contacted