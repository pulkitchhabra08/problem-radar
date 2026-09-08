import json
import os
import re
import urllib.request
import urllib.error

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ProblemRadar/1.0"

SUBREDDITS = ["SaaS", "startups", "entrepreneur", "smallbusiness", "webdev"]
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search?query=%22I%20wish%20there%20was%22%20OR%20%22pain%20point%22&tags=story&numericFilters=created_at_i>"

# Pain-point trigger phrases
TRIGGER_PHRASES = [
    r"i wish there was",
    r"why is there no",
    r"the hardest part about",
    r"is there an alternative to",
    r"i hate when",
    r"struggling with",
    r"any tool that can",
    r"spent hours trying to",
]
TRIGGER_REGEX = re.compile("|".join(TRIGGER_PHRASES), re.IGNORECASE)

def fetch_reddit_posts():
    extracted = []
    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                posts = data.get("data", {}).get("children", [])
                for p in posts:
                    post = p["data"]
                    title = post.get("title", "")
                    selftext = post.get("selftext", "")
                    full_text = f"{title}\n{selftext}"

                    if TRIGGER_REGEX.search(full_text):
                        extracted.append({
                            "id": f"reddit_{post.get('id')}",
                            "source": f"r/{sub}",
                            "title": title,
                            "body": selftext[:1000],  # trim to save token limit
                            "upvotes": post.get("ups", 0),
                            "comments": post.get("num_comments", 0),
                            "url": f"https://reddit.com{post.get('permalink')}",
                        })
        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")
    return extracted

def fetch_hn_posts():
    # HN Algolia API: search for complaints in the last 7 days
    import time
    seven_days_ago = int(time.time()) - (7 * 86400)
    url = f"{HN_SEARCH_URL}{seven_days_ago}"
    extracted = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                text = hit.get("story_text") or ""
                extracted.append({
                    "id": f"hn_{hit.get('objectID')}",
                    "source": "Hacker News",
                    "title": title,
                    "body": text[:1000],
                    "upvotes": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                })
    except Exception as e:
        print(f"Error fetching Hacker News: {e}")
    return extracted

if __name__ == "__main__":
    raw_posts = fetch_reddit_posts() + fetch_hn_posts()
    print(f"Found {len(raw_posts)} candidate complaint posts.")
    os.makedirs("data", exist_ok=True)
    with open("data/raw_posts.json", "w") as f:
        json.dump(raw_posts, f, indent=2)
