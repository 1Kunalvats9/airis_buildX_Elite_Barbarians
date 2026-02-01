# ─────────────────────────────────────────────
# 1. GOOGLE SHEETS SETUP
# ─────────────────────────────────────────────
# Path to your Google Service Account credentials JSON or OAuth Client Secret
GOOGLE_CREDENTIALS_FILE = "credentials.json"

# The ID of your Google Sheet (from the URL)
GOOGLE_SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"

# Sheet names (tabs) - script will auto-create these if missing
SHEET_ALL_BUSINESSES = "All Businesses"
SHEET_LEADS          = "Leads"

# ─────────────────────────────────────────────
# 2. GMAIL — SMTP for sending, IMAP for reading
# ─────────────────────────────────────────────
GMAIL_ADDRESS  = "your-email@gmail.com"
# Generate an App Password at: https://myaccount.google.com/apppasswords
# (requires 2FA to be ON)
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

# ─────────────────────────────────────────────
# 3. GROQ — Free LLM API
# ─────────────────────────────────────────────
# Sign up at https://console.groq.com and grab a free API key
GROQ_API_KEY = "gsk_..."
GROQ_MODEL   = "llama-3.1-8b-instant"

# ─────────────────────────────────────────────
# 4. SCRAPING — Rotating niches & cities
# ─────────────────────────────────────────────
NICHES = [
    "cafe",
    "photographer",
    "boutique",
    "accountant",
    "gym",
]

CITIES = [
    "New York",
    "London",
    "Bangalore",
    "Sydney",
    "Toronto",
]

# ─────────────────────────────────────────────
# 5. POLLING CONFIG
# ─────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 120
