import requests
import time

def login(handle, password):
    auth_response = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password}
    )

    if auth_response.status_code != 200:
        print("Login failed:", auth_response.text)
        exit()

    token = auth_response.json()["accessJwt"]
    print("Logged in successfully!")
    return token



def fetch_posts(token, query, target_bytes):
    # without headers, API request returned 403 Forbidden
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "BlueskySearchBot/1.0"
    }

    cursor = None
    total_bytes = 0
    post_count = 0

    print(f"\nFetching posts about '{query}'...\n")

    while total_bytes < target_bytes:
        params = {"q": query, "limit": 100}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts",
            params=params,
            headers=headers
        )

        if response.status_code != 200:
            print("Error:", response.text)
            break

        data = response.json()
        posts = data.get("posts", [])
        cursor = data.get("cursor")

        if not posts:
            print("No more posts available.")
            break

        for post in posts:
            yield post
            total_bytes += len(str(post).encode("utf-8"))
            post_count += 1

        print(f"Posts fetched: {post_count} | Data collected: {total_bytes / 1024 / 1024:.2f} MB")

        if not cursor:
            print("Reached end of search results.")
            break

        time.sleep(0.5)