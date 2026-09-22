import requests
import json
import os

# --- CONFIGURATION ---
TARGET_HANDLE = "futdonk"
API_URL = f"https://api.fxtwitter.com/{TARGET_HANDLE}"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

KEYWORDS = ["ea sports", "direct", "update", "fut", "toty", "tots", "sbc"]  # Customize keywords (lowercase)
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
    print(f"Fetching profile data for @{TARGET_HANDLE}...")
    last_seen = load_last_seen()
    
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(API_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch profile API. Status code: {response.status_code}")
        return

    data = response.json()
    
    # Debug print to confirm API connection
    print(f"API Response keys received: {list(data.keys())}")

    # FxTwitter nests timelines under different keys depending on profile layout
    tweet_container = data.get("tweets", [])
    if not tweet_container and "user" in data:
        # Some profile queries return user details; check for pinned or timeline fallback
        tweet_container = data.get("user", {}).get("tweets", [])

    # If it's a single tweet dictionary fallback
    if not tweet_container and "tweet" in data:
        tweet_container = [data["tweet"]]

    if not tweet_container:
        print("Timeline array is empty or restricted for this handle.")
        return

    new_seen = list(last_seen)
    found_new = False

    for tweet in reversed(tweet_container):
        tweet_id = str(tweet.get("id"))
        
        if tweet_id in last_seen:
            continue
            
        tweet_text = tweet.get("text", "")
        tweet_link = tweet.get("url", f"https://twitter.com/{TARGET_HANDLE}")
        
        media_url = None
        media = tweet.get("media", {})
        photos = media.get("photos", [])
        if photos:
            media_url = photos[0].get("url")

        full_text = tweet_text.lower()
        if any(kw.lower() in full_text for kw in KEYWORDS):
            print(f"Match found! Sending to Discord: {tweet_text[:40]}...")
            send_to_discord(tweet_text, tweet_link, media_url)
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
