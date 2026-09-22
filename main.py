import requests
import json
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TARGET_HANDLE = "Futdonk"
PAGE_URL = f"https://vxtwitter.com/{TARGET_HANDLE}"

# Pulls the webhook securely from GitHub Actions Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

KEYWORDS = ["6pm"]  # Customize your lowercase keywords here
LAST_SEEN_FILE = "last_seen.json"

def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        try:
            with open(LAST_SEEN_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_last_seen(seen_list):
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump(seen_list[-50:], f)

def send_to_discord(tweet_text, tweet_link, media_url):
    embed = {
        "title": f"New @{TARGET_HANDLE} Post Match",
        "description": tweet_text,
        "url": tweet_link,
        "color": 16711680,  # Red theme color
        "fields": [
            {"name": "Original Post", "value": f"[View on X]({tweet_link})", "inline": False}
        ]
    }
    
    if media_url:
        embed["image"] = {"url": media_url}

    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if response.status_code == 204:
        print("Successfully posted tweet to Discord!")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}")

def main():
    print(f"Scraping timeline for @{TARGET_HANDLE} using BeautifulSoup...")
    last_seen = load_last_seen()
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(PAGE_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    
    meta_desc = soup.find("meta", property="og:description")
    meta_image = soup.find("meta", property="og:image")
    
    if not meta_desc:
        print("Could not parse posts via BeautifulSoup.")
        return
        
    tweet_text = meta_desc.get("content", "")
    media_url = meta_image.get("content", "") if meta_image else None
    tweet_link = f"https://twitter.com/{TARGET_HANDLE}"
    
    tweet_id = str(hash(tweet_text))
    
    if tweet_id in last_seen:
        print("No new unique posts found.")
        return
        
    full_text = tweet_text.lower()
    if any(kw.lower() in full_text for kw in KEYWORDS):
        print("Match found! Sending to Discord...")
        send_to_discord(tweet_text, tweet_link, media_url)
        
    save_last_seen(last_seen + [tweet_id])
    print("State updated successfully.")

if __name__ == "__main__":
    main()
