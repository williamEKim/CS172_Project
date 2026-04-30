from Bluesky import login, fetch_posts, extract_urls, fetch_titles
from getpass import getpass
import os, json

# TARGET_SIZE = 500 * 1024 * 1024   # 500MB
TARGET_SIZE = 3 * 1024 * 1024      # set it to 3MB for now (testing purpose)
# FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB per file
FILE_SIZE_LIMIT = 3 * 1024 * 1024  # 3MB per file
OUTPUT_DIR = "./raw_files"

def main():
    handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
    password = getpass("Enter your Bluesky app password: ")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_index = 1
    file_size = 0
    
    token = login(handle, password)
    if not token:
        return

    query = input("Enter search term: ")

    file = open(f"{OUTPUT_DIR}/bluesky_{query}_{file_index}.jsonl", "w")

    posts = fetch_posts(token, query, TARGET_SIZE)

    for post in posts:
        extract_urls(post)
        fetch_titles(post)

        line = json.dumps(post) + "\n"
        line_size = len(line.encode("utf-8"))
        
        if file_size + line_size > FILE_SIZE_LIMIT: # currently 3MB for testing
            file.close()
            file_size = 0
            file_index += 1
            file = open(f"{OUTPUT_DIR}/bluesky_{query}_{file_index}.jsonl", "w")

        file.write(line)
        file_size += line_size
            
    file.close()

    # collected = list(posts)

    print("Data Collection is completed:")
    # print(f"Data collection completed: {len(collected)} posts fetched")
    # print("\nSample post:")
    # print(collected[0])

    # process_posts() # needs to be implemented

if __name__ == "__main__":
    main()