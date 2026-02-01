# AI Client Finder Agent

An autonomous AI agent that finds freelance leads, sends personalized cold emails, and tracks replies.

## Features

- **Scrape:** Finds local businesses (that don't have websites) using specific niche/city combinations.
- **Store:** Saves prospects to Google Sheets.
- **Email:** Generates personalized cold emails using AI (Groq/Llama 3) and sends them via Gmail.
- **Track:** Polls your inbox for replies, classifies them using AI (Interested/Not Interested), and updates the sheet.

## Prerequisites

1.  **Python 3.10+**
2.  **Google Cloud Platform Project** with **Google Sheets API** enabled.
    *   Download `credentials.json` (OAuth 2.0 Client ID) and place it in the project root.
3.  **Gmail Account** with 2-Factor Authentication enabled.
    *   Generate an App Password: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4.  **Groq API Key** (for free LLM access).
    *   Get one here: [https://console.groq.com](https://console.groq.com)

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You may need to create a `requirements.txt` with: `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`, `groq`, `beautifulsoup4`, `requests`)*

3.  **Configuration:**
    *   Rename `example_config.py` to `config.py`.
    *   Fill in your API keys, Email credentials, and Sheet ID.

## Usage

### 1. Run the Full Agent
Runs the entire cycle: Scrape -> Email -> Poll once.
```bash
python main.py
```

### 2. Specific Modes
Run only specific parts of the pipeline:

**Scrape Only:**
```bash
python main.py scrape
```

**Email Pending Leads:**
```bash
python main.py email
```

**Continuous Polling (Reply Tracker):**
```bash
python main.py poll
```

## Folder Structure

- `main.py`: Master orchestrator.
- `scraper.py`: Logic for finding businesses.
- `ai.py`: AI Brain (Email generation & Reply classification).
- `sheets.py`: Google Sheets API handler.
- `lead_tracker.py`: Gmail IMAP handler for reading replies.
- `email_sender.py`: Gmail SMTP handler for sending emails.
