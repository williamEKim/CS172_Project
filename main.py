from Bluesky import login, fetch_posts, extract_urls, fetch_titles
from process import process_post, save_posts, save_raw_posts
from getpass import getpass
import requests
import json
import os


TARGET_SIZE = 500 * 1024 * 1024
FILE_SIZE_LIMIT = 10 * 1024 * 1024

QUERIES = [
    "baseball", "football", "hockey", "volleyball", "golf", "cricket", "rugby", "skiing", "snowboarding", "tennis", "boxing", "mma", "wrestling", "cycling",
    "chess", "esports", "darts", "badminton", "pool", "ice skating", "rowing", "surfing"
]

GeminiAPI = ( "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

def summarize(apiKey, query, posts: list[dict]) -> str:
    lines = []
    charsCount = 0

    for i, post in enumerate(posts,1):
        text = (post.get("text") or "").strip()
        if not text:
            continue
        entry = f"{i}. {text}"
        if charsCount +len(entry) > 40000:
            break
        lines.append(entry)
        charsCount += len(entry)

    if not lines:
        return "No text to summarize"
    
    postBlock = "\n".join(lines)
    prompt = (f"Summarize the following posts about {query} in 3 sentences:\n\n{postBlock}")

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(
            GeminiAPI,
            params = {"key": apiKey},
            headers={"Content_type": "application/json"},
            json = payload,
            timeout = 60
        )

        response.raise_for_status()
        data = response.json()

        summary = (
            data.get("choices", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        return summary if summary else "No summary generated"
    
    except requests.exceptions.HTTPError as e:
        return f"Gemini API error: {e.response.status_code} - {e.response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Request error: {str(e)}"
    
    except (json.JSONDecodeError, KeyError) as e:
        return f"Response parsing error: {str(e)}"
    

def saveSummary(summary: str, output_dir: str, query: str):
    summary_dir = os.path.join(output_dir, "summaries")
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, f"{query}_summary.txt")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"Summarized by Gemini: ")
        f.write(summary)
        f.write("\n")

    print(f"Summary saved to {summary_path}")

def main():
    handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
    password = getpass("Enter your Bluesky app password: ")

    token = login(handle, password)
    if not token:
        return

    output_dir = input("Enter output directory: ")
    raw_dir = os.path.join(output_dir, "raw")
    summary_dir = os.path.join(output_dir, "summaries")

    geminiAPIkey = input("Enter your Gemini API key: ").strip()

    
    for query in QUERIES:
        raw_posts_list = []
        processed = []

        print(f"\nStarting query: {query}")
        raw_posts = fetch_posts(token, query, TARGET_SIZE, handle, password)

        for post in raw_posts:
            raw_posts_list.append(post)
            extract_urls(post)
            processed.append(process_post(post))
        
        fetch_titles(processed)
        save_posts(processed, output_dir, query)
        save_raw_posts(raw_posts_list, raw_dir, query)
        print(f"Finished query: {query}")

        if geminiAPIkey:
            print(f"Summarizing posts for query: {query}")
            summary = summarize(geminiAPIkey, query, processed)
            saveSummary(summary, summary_dir, query)
    
    print("\nAll queries done.")

if __name__ == "__main__":
    main()
