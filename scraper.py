import json
import os
import urllib.request
import urllib.error

USER_AGENT = "ProblemRadar/1.0 (free open-source scraper; contact@problemradar.dev)"

def fetch_hn_problems():
    """Hacker News Ask HN threads about tools, struggles, and unmet needs."""
    queries = [
        "Ask HN: What is your biggest pain point",
        "Ask HN: What software do you wish existed",
        "Ask HN: frustrating tool",
        "Ask HN: struggle with",
    ]
    extracted = []
    
    for query in queries:
        encoded_query = urllib.parse.quote(query)
        url = f"https://hn.algolia.com/api/v1/search?query={encoded_query}&tags=story&hitsPerPage=20"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for hit in data.get("hits", []):
                    title = hit.get("title") or ""
                    text = hit.get("story_text") or ""
                    
                    if len(title) > 15:
                        extracted.append({
                            "id": f"hn_{hit.get('objectID')}",
                            "source": "Hacker News",
                            "title": title,
                            "body": (text or title)[:1000],
                            "upvotes": hit.get("points") or 1,
                            "comments": hit.get("num_comments") or 0,
                            "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        })
        except Exception as e:
            print(f"Error fetching HN query '{query}': {e}")
            
    return extracted

def fetch_devto_complaints():
    """Dev.to articles discussing developer tool headaches and problems."""
    url = "https://dev.to/api/articles?tag=productivity&top=30"
    extracted = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for article in data:
                title = article.get("title", "")
                desc = article.get("description", "")
                if any(w in (title + desc).lower() for w in ["hate", "problem", "hardest", "struggle", "why", "waste"]):
                    extracted.append({
                        "id": f"devto_{article.get('id')}",
                        "source": "Dev.to",
                        "title": title,
                        "body": desc[:1000],
                        "upvotes": article.get("positive_reactions_count", 1),
                        "comments": article.get("comments_count", 0),
                        "url": article.get("url"),
                    })
    except Exception as e:
        print(f"Error fetching Dev.to: {e}")
    return extracted

if __name__ == "__main__":
    posts = fetch_hn_problems() + fetch_devto_complaints()
    print(f"Successfully collected {len(posts)} candidate problem posts.")
    
    os.makedirs("data", exist_ok=True)
    with open("data/raw_posts.json", "w") as f:
        json.dump(posts, f, indent=2)
