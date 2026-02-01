"""
scraper.py — Searches DuckDuckGo for local businesses in a niche+city combo,
then filters to keep only those that likely DON'T have a website.
"""

import random
import re
import time
import socket
from ddgs import DDGS
from config import NICHES, CITIES, RESULTS_PER_QUERY, COMBOS_PER_CYCLE


# ─────────────────────────────────────────────
# Pick random niche + city combos
# ─────────────────────────────────────────────
def get_random_combos(n=COMBOS_PER_CYCLE):
    combos = []
    for _ in range(n):
        niche = random.choice(NICHES)
        city  = random.choice(CITIES)
        combos.append((niche, city))
    print(f"[SCRAPER] Selected {n} combos: {combos}")
    return combos


# ─────────────────────────────────────────────
# Extract a domain from a snippet / URL if present
# ─────────────────────────────────────────────
def extract_domain(url: str) -> str | None:
    """Pull the root domain out of a URL string."""
    try:
        match = re.search(r"https?://([^/\s]+)", url)
        if match:
            domain = match.group(1).lower()
            # skip social media / directories — these aren't "their own" website
            skip = ["facebook.com", "instagram.com", "twitter.com",
                    "yelp.com", "google.com", "maps.google.com",
                    "justdial.com", "sulekha.com", "indiamart.com",
                    "urbanclap.com", "urban company", "linkedin.com"]
            for s in skip:
                if s in domain:
                    return None
            return domain
    except Exception:
        pass
    return None


def has_own_website(domain: str) -> bool:
    """Quick DNS check — if the domain resolves, they probably have a site."""
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo(domain, 80)
        return True
    except (socket.gaierror, socket.timeout):
        return False


# ─────────────────────────────────────────────
# Core scrape function
# ─────────────────────────────────────────────
def scrape_businesses(niche: str, city: str) -> list[dict]:
    """
    Search DuckDuckGo for businesses matching niche+city.
    Return a list of dicts for businesses that appear to have NO website.
    """
    query = f"{niche} in {city} contact"
    print(f"[SCRAPER] Searching: '{query}'")

    results = []
    try:
        with DDGS() as ddgs:
            hits = ddgs.text(query, max_results=RESULTS_PER_QUERY)
            results = list(hits) if hits else []
    except Exception as e:
        print(f"[SCRAPER] Search error: {e}")
        return []

    businesses = []
    seen_titles = set()

    for r in results:
        title   = r.get("title", "").strip()
        body    = r.get("body", "").strip()
        url     = r.get("href", "").strip()

        # deduplicate
        if title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        # skip obvious non-business results (news, wiki, etc.)
        skip_keywords = ["wikipedia", "news", "article", "blog", "how to", "what is", "top 10", "best in"]
        if any(kw in title.lower() or kw in body.lower() for kw in skip_keywords):
            continue

        # Check if they have their own website
        domain = extract_domain(url)
        if domain and has_own_website(domain):
            # They already have a website → not our target
            print(f"  [SKIP] {title} — has website ({domain})")
            continue

        # This business likely has NO website — it's a candidate
        businesses.append({
            "business_name": title,
            "niche":         niche,
            "city":          city,
            "source_url":    url,
            "snippet":       body[:200],  # first 200 chars of description
            "has_website":   "No",
            "status":        "Pending",   # Pending → Contacted → Lead
            "email_sent":    "No",
            "notes":         "",
        })
        print(f"  [FOUND] {title} — no website detected")

    print(f"[SCRAPER] Found {len(businesses)} candidate(s) for '{niche} in {city}'")
    return businesses


# ─────────────────────────────────────────────
# Run full scrape cycle
# ─────────────────────────────────────────────
def run_scrape_cycle() -> list[dict]:
    """Run scrapes for all random combos and return combined results."""
    combos = get_random_combos()
    all_businesses = []

    for niche, city in combos:
        businesses = scrape_businesses(niche, city)
        all_businesses.extend(businesses)
        time.sleep(2)  # be polite to DuckDuckGo

    print(f"\n[SCRAPER] Total businesses collected this cycle: {len(all_businesses)}")
    return all_businesses