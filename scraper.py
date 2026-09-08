import json
import os
import re
import urllib.request
import urllib.error

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ProblemRadar/1.0"

SUBREDDITS = ["SaaS", "startups", "entrepreneur", "smallbusiness", "webdev", "sideproject"]

# Broader keywords to capture complaints and feature gaps
TRIGGER_WORDS = [
    "problem", "issue", "struggling", "hardest", "hate", "wish", 
    "alternative", "missing", "automate", "manual", "waste", "frustrated",
    "annoying", "pain", "looking for a tool"
]
TRIGGER_REGEX = re.compile(r"\b(" + "|".join(TRIGGER_WORDS) + r")\b", re.IGNORECASE)

def fetch_reddit_posts():
    extracted = []
    for sub in SUBREDDITS:
        # Fetch top posts from the past month for much higher quality signals
        url = f"https://www.reddit.com/r/{sub}/top.json?t=month&limit=50"
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

                    # Exclude mod posts or empty bodies
                    if post.get("stickied") or len(full_text.strip()) < 40:
                        continue

                    if TRIGGER_REGEX.search(full_text):
                        extracted.append({
                            "id": f"reddit_{post.get('id')}",
                            "source": f"r/{sub}",
                            "title": title,
                            "body": selftext[:1200],
                            "upvotes": post.get("ups", 0),
                            "comments": post.get("num_comments", 0),
                            "url": f"https://reddit.com{post.get('permalink')}",
                        })
        except Exception as e:
            print(f"Error fetching r/{sub}: {e}")
    return extracted

def fetch_hn_posts():
    import time
    month_ago = int(time.time()) - (30 * 86400)
    # Search Ask HN posts discussing tools and frustrations
    url = f"https://hn.algolia.com/api/v1/search?query=Ask%20HN%20problem%20OR%20struggle%20OR%20%22pain%20point%22&tags=story&numericFilters=created_at_i>{month_ago}"
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
                    "body": text[:1200],
                    "upvotes": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
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
