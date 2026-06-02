from Bluesky import login, fetch_posts, extract_urls, fetch_titles
from process import process_post, save_posts, save_raw_posts
from getpass import getpass
import os


TARGET_SIZE = 500 * 1024 * 1024
FILE_SIZE_LIMIT = 10 * 1024 * 1024

QUERIES = [
    "baseball", "football", "hockey", "volleyball", "golf", "cricket", "rugby", "skiing", "snowboarding", "tennis", "boxing", "mma", "wrestling", "cycling",
    "chess", "esports", "darts", "badminton", "pool", "ice skating", "rowing", "surfing"
]


def main():
    handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
    password = getpass("Enter your Bluesky app password: ")

    token = login(handle, password)
    if not token:
        return

    output_dir = input("Enter output directory: ")
    raw_dir = os.path.join(output_dir, "raw")

    
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
    
    print("\nAll queries done.")

if __name__ == "__main__":
    main()
