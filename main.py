import requests
import json
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
TARGET_HANDLE = "futdonk"
# Using a clean public RSS bridge that exposes recent timeline items
FEED_URL = f"https://nitter.poast.org/{TARGET_HANDLE}/rss"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

KEYWORDS = ["6pm"]  # Customize lowercase keywords here
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

def send_to_discord(tweet_text, tweet_link):
    embed = {
        "title": f"New @{TARGET_HANDLE} Post Match",
        "description": tweet_text,
        "url": tweet_link,
        "color": 16711680,  # Red theme color
        "fields": [
            {"name": "Original Post", "value": f"[View on X]({tweet_link})", "inline": False}
        ]
    }

    payload = {"embeds": [embed]}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    if response.status_code == 204:
        print("Successfully posted tweet to Discord!")
    else:
        print(f"Failed to post to Discord. Status code: {response.status_code}")

def main():
    print(f"Fetching feed for @{TARGET_HANDLE}...")
    last_seen = load_last_setup = load_last_seen()
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(FEED_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch feed. Status code: {response.status_code}")
        return

    # Parse XML feed layout
    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")
    
    if not items:
        print("No items found in feed.")
        return

    new_seen = list(last_seen)
    found_new = False

    for item in reversed(items):
        title_tag = item.find("title")
        link_tag = item.find("link")
        guid_tag = item.find("guid")
        
        tweet_text = title_tag.text if title_tag else ""
        tweet_link = link_tag.text if link_tag else f"https://twitter.com/{TARGET_HANDLE}"
        # Fallback unique identifier based on link or GUID
        tweet_id = guid_tag.text if guid_tag else tweet_link
        
        if tweet_id in last_seen:
            continue
            
        full_text = tweet_text.lower()
        if any(kw.lower() in full_text for kw in KEYWORDS):
            print(f"Match found! Sending to Discord: {tweet_text[:40]}...")
            send_to_discord(tweet_text, tweet_link)
        else:
            print(f"Skipped (no keyword match): {tweet_text[:40]}...")
            
        new_seen.append(tweet_id)
        found_new = True

    if found_new:
        save_last_seen(new_seen)
        print("State updated successfully.")
    else:
        print("No new posts to process.")

if __name__ == "__main__":
    main()
