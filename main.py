from Bluesky import login, fetch_posts, extract_urls, fetch_titles
from process import process_post, save_posts, save_raw_posts
from getpass import getpass
import requests
import json
import os
import glob
import time 

TARGET_SIZE = 500 * 1024 * 1024
FILE_SIZE_LIMIT = 10 * 1024 * 1024

QUERIES = [
    "baseball", "football", "hockey", "volleyball", "golf", "cricket", "rugby", "skiing", "snowboarding", "tennis", "boxing", "mma", "wrestling", "cycling",
    "chess", "esports", "darts", "badminton", "pool", "ice skating", "rowing", "surfing"
]

GeminiAPI = ( "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

def summarize(apiKey, post: dict) -> str:
    text = (post.get("text") or "").strip()
    if not text:
        return "No text to summarize"
    

    urlTitles = [item["title"] for item in post.get("url_data",[]) if item.get("title")]
    context = ("\nLinked pages: " + "; ".join(urlTitles)) if urlTitles else ""

    prompt = (f"Summarize the most important parts of the following sports related post in 5 bulletpoints:"
              f"Make the reply only the summary and nothing else \n\n"
              f"Post: {text}{context}\n")

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        response = requests.post(
            GeminiAPI,
            params = {"key": apiKey},
            headers={"Content-Type": "application/json"},
            json = payload,
            timeout = 60
        )

        response.raise_for_status()
        data = response.json()

        summary = (
            data.get("candidates", [{}])[0]
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
    

def saveSummary(posts: list[dict], output_dir: str, query: str):
    summary_dir = os.path.join(output_dir, "summaries")
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, f"{query}_summary.txt")

    with open(summary_path, "w", encoding="utf-8") as f:
        for post in posts:
            record = {
                "Author": post.get("author_handle"),
                "Created:": post.get("created_at"),
                "Text": post.get("text"),
                "Summary": post.get("summary")
            }
            f.write(json.dumps(record) + "\n")

    print(f"Summary saved to {summary_path}")

def loadProcessedPosts(processed_dir: str, query: str) -> list[dict]:
    pattern = os.path.join(processed_dir, f"bluesky_{query}_*.jsonl")
    files = sorted(glob.glob(pattern))
 
    if not files:
        print(f"  No files found for query '{query}' in {processed_dir}")
        return []
 
    posts = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    posts.append(json.loads(line))
 
    print(f"  Loaded {len(posts)} posts from {len(files)} file(s) for query '{query}'")
    return posts
 
 
def runSummarization(geminiAPIkey: str, output_dir: str, processed_dir: str):
    for query in QUERIES:
        print(f"\nSummarizing query: {query}")
        processed = loadProcessedPosts(processed_dir, query)
 
        if not processed:
            continue
 
        for i, post in enumerate(processed[:1], 1):
            post["summary"] = summarize(geminiAPIkey, post)
            print(f"  [{i}/{len(processed)}] {post['summary'][:80] or '(no text, skipped)'}")
            time.sleep(1)
 
        saveSummary(processed, output_dir, query)
 
    print("\nAll summaries done.")

def main():

    skipCrawl = input("Skip crawling and just summarize existing posts? (y/n): ").strip().lower() == "y"

    if skipCrawl:
        processed_dir = input("Enter directory of processed posts: ")
        output_dir = input("Enter output directory for summaries: ")
        geminiAPIkey = input("Enter your Gemini API key: ").strip()

        runSummarization(geminiAPIkey, output_dir, processed_dir)

    else:
        handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
        password = getpass("Enter your Bluesky app password: ")

        token = login(handle, password)
        if not token:
            return

        output_dir = input("Enter output directory: ")
        raw_dir = os.path.join(output_dir, "raw")

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

                for i, post in enumerate(processed,1):
                    post["summary"] = summarize(geminiAPIkey, post)
                    print(f"Summarized {i}/{len(processed)} posts...")
            
                saveSummary(processed, output_dir, query)
    
    print("\nAll queries done.")

if __name__ == "__main__":
    main()
