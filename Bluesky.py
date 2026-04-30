import requests
import time
import json
from bs4 import BeautifulSoup

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



def extract_urls(post):
    urls = []

    facets = post.get("record", {}).get("facets", [])
    for facet in facets:
        features = facet.get("features", [])
        for feature in features:
            if feature.get("$type") == "app.bsky.richtext.facet#link":
                urls.append(feature.get("uri"))

    embed = post.get("record", {}).get("embed", {})
    external = embed.get("external") or post.get("embed", {}).get("external")
    if external and external.get("uri"):
        urls.append(external["uri"])

    urls = list(dict.fromkeys(urls))

    post["url_data"] = [
        {"url": url, "title": None}
        for url in urls
    ]



_url_count = 0
def fetch_titles(post):
    global _url_count

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url_data = post.get("url_data", [])
    
    if url_data:
        for item in url_data:
            url = item["url"]

            if not url: # empty url list
                continue

            if "bit.ly" in url: # short links
                print("Skipping bit.ly links")
                continue

            try:
                page = requests.get(url, timeout=5, headers=headers)
                soup = BeautifulSoup(page.content, "html.parser")
                title = soup.title
                if title:
                    item["title"] = title.string
                    _url_count += 1
                    print(f"Successful URL Count: {_url_count}")
                else:
                    # no title for page
                    item["title"] = None

            except requests.exceptions.Timeout:
                item["title"] = None
                print(f"Timeout: {url}")
                continue

            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
     