import re
import aiohttp

def extract_urls(text):
    return re.findall(r'(https?://[^\s]+)', text)

async def is_phishing(url):
    # Simple check for demo
    blacklisted = ["free-nitro", "steam-gift", "gift-card"]
    for word in blacklisted:
        if word in url.lower():
            return True, f"Blacklisted word: {word}"
    return False, None
