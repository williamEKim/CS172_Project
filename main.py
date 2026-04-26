from Bluesky import login, fetch_posts
from getpass import getpass

# TARGET_SIZE = 500 * 1024 * 1024   # 500MB
TARGET_SIZE = 3 * 1024 * 1024      # set it to 3MB for now (testing purpose)
FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB per file

def main():
    handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
    password = getpass("Enter your Bluesky app password: ")

    token = login(handle, password)
    if not token:
        return

    query = input("Enter search term: ")

    posts = fetch_posts(token, query, TARGET_SIZE)

    collected = list(posts)

    print("Data Collection is completed:")
    print(f"Data collection completed: {len(collected)} posts fetched")
    print("\nSample post:")
    print(collected[0])

    # process_posts() # needs to be implemented

if __name__ == "__main__":
    main()