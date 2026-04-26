from Bluesky import login, fetch_posts

TARGET_SIZE = 500 * 1024 * 1024   # 500MB
FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB per file

def main():
    handle = input("Enter your Bluesky handle (e.g. yourname.bsky.social): ")
    password = input("Enter your Bluesky app password: ")

    token = login(handle, password)
    if not token:
        return

    query = input("Enter search term: ")

    posts = fetch_posts(token, query, TARGET_SIZE)
    # process_posts() # needs to be implemented

if __name__ == "__main__":
    main()