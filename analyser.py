import json
import os
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY missing. Skipping AI processing.")
    exit(0)

client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT_TEMPLATE = """
You are an expert product researcher. Analyze this forum post and determine if there is a genuine, actionable software/tool pain point or unmet need.

Post Title: {title}
Post Content: {body}

If this is a valid pain point or software need, output a JSON object with:
- "is_valid": true
- "problem_title": "Short, catchy summary of the problem (max 10 words)"
- "problem_description": "2-3 sentences clearly explaining the frustration"
- "target_audience": "Who experiences this? (e.g. Freelancers, Devs, E-commerce owners)"
- "category": "One of: Productivity, Developer Tools, Marketing, Operations, AI/Automation, Other"
- "difficulty_to_build": "Easy | Medium | Hard"

If it is just chit-chat, a self-promotion post, or has no software problem, output:
{{"is_valid": false}}

Only output valid JSON, no markdown codeblocks, no explanations.
"""

def analyze():
    if not os.path.exists("data/raw_posts.json"):
        return

    with open("data/raw_posts.json", "r") as f:
        raw_posts = json.load(f)

    # Load existing problems to avoid duplicates
    existing = []
    if os.path.exists("data/problems.json"):
        with open("data/problems.json", "r") as f:
            existing = json.load(f)

    existing_ids = {p.get("id") for p in existing}
    analyzed_problems = list(existing)

    # Limit to 15 at a time to stay well within free RPM limits
    for post in raw_posts[:15]:
        if post["id"] in existing_ids:
            continue

        try:
            prompt = PROMPT_TEMPLATE.format(title=post["title"], body=post["body"])
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            res_json = json.loads(response.text)
            if res_json.get("is_valid"):
                analyzed_problems.insert(0, {
                    "id": post["id"],
                    "title": res_json.get("problem_title"),
                    "description": res_json.get("problem_description"),
                    "audience": res_json.get("target_audience"),
                    "category": res_json.get("category"),
                    "difficulty": res_json.get("difficulty_to_build"),
                    "source": post["source"],
                    "url": post["url"],
                    "upvotes": post["upvotes"],
                    "comments": post["comments"]
                })
                print(f"Validated problem: {res_json.get('problem_title')}")
        except Exception as e:
            print(f"Error analyzing {post['id']}: {e}")

    # Keep top 100 newest/most upvoted
    with open("data/problems.json", "w") as f:
        json.dump(analyzed_problems[:100], f, indent=2)

if __name__ == "__main__":
    analyze()
